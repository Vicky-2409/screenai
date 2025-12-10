"""Resume text extraction and structured field normalization."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

from app.core.logging import get_logger
from app.services.skills_db import extract_skills_from_text

logger = get_logger(__name__)


@lru_cache
def _load_spacy():
    """Lazily load the spaCy English model.

    Returns ``None`` if spaCy or the model is unavailable so parsing always
    falls back to regex heuristics and the app keeps working.
    """
    try:
        import spacy

        return spacy.load("en_core_web_sm")
    except Exception as exc:  # noqa: BLE001
        logger.warning("spaCy model unavailable, using regex-only parsing: %s", exc)
        return None


def _spacy_entities(text: str) -> dict[str, list[str]]:
    """Extract PERSON / GPE-LOC / ORG entities from the top of the resume."""
    nlp = _load_spacy()
    if nlp is None:
        return {}
    # Only run NER over the header region for speed and relevance.
    doc = nlp(text[:2000])
    entities: dict[str, list[str]] = {"PERSON": [], "LOC": [], "ORG": []}
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["PERSON"].append(ent.text.strip())
        elif ent.label_ in ("GPE", "LOC"):
            entities["LOC"].append(ent.text.strip())
        elif ent.label_ == "ORG":
            entities["ORG"].append(ent.text.strip())
    return entities

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
EXPERIENCE_RE = re.compile(r"(\d{1,2})\+?\s*(?:years|yrs|year)", re.IGNORECASE)
DEGREE_RE = re.compile(
    r"\b(b\.?tech|m\.?tech|b\.?sc|m\.?sc|b\.?e\.?|m\.?e\.?|bachelor|master|mba|ph\.?d|"
    r"b\.?a\.?|m\.?a\.?|bca|mca|diploma)\b",
    re.IGNORECASE,
)

SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic", "qualifications"],
    "skills": ["skills", "technical skills", "core competencies"],
    "projects": ["projects", "personal projects", "key projects"],
    "certifications": ["certifications", "certificates", "licenses"],
}


@dataclass
class ParsedResume:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    designation: str | None = None
    total_experience_years: float = 0.0
    skills: list[str] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    experience: list[dict] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def extract_text(path: str, content_type: str | None = None) -> str:
    """Extract plain text from a PDF, DOCX or TXT file."""
    suffix = Path(path).suffix.lower()
    try:
        if suffix == ".pdf":
            return _extract_pdf(path)
        if suffix in (".docx", ".doc"):
            return _extract_docx(path)
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Text extraction failed for %s: %s", path, exc)
        return ""


def _extract_pdf(path: str) -> str:
    text = ""
    # Primary: PyMuPDF (fast, robust).
    try:
        import fitz  # PyMuPDF

        with fitz.open(path) as doc:
            text = "\n".join(page.get_text() for page in doc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("PyMuPDF failed (%s), trying pdfplumber", exc)

    # Fallback: pdfplumber (better with some layouts).
    if len(text.strip()) < 30:
        try:
            import pdfplumber

            with pdfplumber.open(path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as exc:  # noqa: BLE001
            logger.warning("pdfplumber failed: %s", exc)
    return text


def _extract_docx(path: str) -> str:
    import docx

    document = docx.Document(path)
    return "\n".join(p.text for p in document.paragraphs)


def _name_from_header(text: str) -> str | None:
    """Find a plausible name in the first few lines (None if no good match)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:5]:
        # A name line is usually short, alphabetic, title-cased.
        words = line.split()
        if 1 < len(words) <= 4 and all(w[0].isupper() for w in words if w[:1].isalpha()):
            if not EMAIL_RE.search(line) and not PHONE_RE.search(line):
                return line
    return None


def _name_from_email(email: str | None) -> str | None:
    if email:
        local = email.split("@")[0]
        return local.replace(".", " ").replace("_", " ").title()
    return None


def _split_sections(text: str) -> dict[str, str]:
    """Best-effort split of the resume into known sections."""
    lines = text.splitlines()
    sections: dict[str, list[str]] = {}
    current = "header"
    sections[current] = []
    for line in lines:
        stripped = line.strip().lower()
        matched = None
        for section, headers in SECTION_HEADERS.items():
            if stripped in headers or any(stripped.startswith(h) and len(stripped) < 30 for h in headers):
                matched = section
                break
        if matched:
            current = matched
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _parse_experience_years(text: str) -> float:
    matches = [int(m) for m in EXPERIENCE_RE.findall(text)]
    return float(max(matches)) if matches else 0.0


def normalize(text: str) -> ParsedResume:
    """Extract and normalize structured fields from resume text."""
    result = ParsedResume(raw_text=text)
    if not text.strip():
        return result

    email_match = EMAIL_RE.search(text)
    result.email = email_match.group(0) if email_match else None

    phone_match = PHONE_RE.search(text)
    if phone_match:
        digits = re.sub(r"\D", "", phone_match.group(0))
        if 8 <= len(digits) <= 15:
            result.phone = phone_match.group(0).strip()

    # Run spaCy NER once over the header region (no-op if model unavailable).
    ents = _spacy_entities(text)

    # Name resolution order: a clear header line wins; otherwise fall back to a
    # spaCy PERSON entity; finally derive from the email local part.
    header_name = _name_from_header(text)
    if header_name:
        result.name = header_name
    elif ents.get("PERSON"):
        result.name = ents["PERSON"][0]
    else:
        result.name = _name_from_email(result.email)

    if ents.get("LOC"):
        result.location = ents["LOC"][0][:120]

    result.total_experience_years = _parse_experience_years(text)
    result.skills = extract_skills_from_text(text)

    sections = _split_sections(text)

    # Education
    edu_text = sections.get("education", "")
    for line in edu_text.splitlines():
        if DEGREE_RE.search(line) and line.strip():
            result.education.append({"detail": line.strip()})

    # Certifications
    cert_text = sections.get("certifications", "")
    result.certifications = [ln.strip("-*  ") for ln in cert_text.splitlines() if ln.strip()][:15]

    # Experience / companies (lightweight)
    exp_text = sections.get("experience", "")
    for line in exp_text.splitlines():
        s = line.strip()
        if s and len(s) < 200 and re.search(r"\b(at|@|inc|llc|ltd|technologies|systems|solutions)\b", s, re.IGNORECASE):
            result.experience.append({"detail": s})
            company = re.split(r"\bat\b|@", s, maxsplit=1, flags=re.IGNORECASE)
            if len(company) > 1:
                result.companies.append(company[1].strip()[:120])
    # Augment companies with spaCy ORG entities found in the header region.
    for org in ents.get("ORG", []):
        if org and org not in result.companies:
            result.companies.append(org[:120])
    result.companies = sorted(set(result.companies))[:10]

    # Projects
    proj_text = sections.get("projects", "")
    for line in proj_text.splitlines():
        s = line.strip("-*  ")
        if s:
            result.projects.append({"detail": s})
    result.projects = result.projects[:15]

    # Designation: try first experience line or header role keywords.
    designation_match = re.search(
        r"\b(senior|lead|principal|junior|staff)?\s*(software|backend|frontend|full[- ]?stack|"
        r"data|ml|devops|cloud|qa|test)?\s*(engineer|developer|scientist|architect|analyst|manager)\b",
        text,
        re.IGNORECASE,
    )
    if designation_match:
        result.designation = re.sub(r"\s+", " ", designation_match.group(0)).strip().title()

    return result


def parse_resume_file(path: str, content_type: str | None = None) -> ParsedResume:
    text = extract_text(path, content_type)
    return normalize(text)
