"""Weighted candidate-to-job scoring.

Overall = 40% semantic + 25% skills + 20% experience + 10% education + 5% keyword
All component scores are normalized to a 0-100 scale.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

from app.services.skills_db import extract_skills_from_text

WEIGHTS = {
    "semantic": 0.40,
    "skills": 0.25,
    "experience": 0.20,
    "education": 0.10,
    "keyword": 0.05,
}

EDUCATION_LEVELS = {
    "phd": 5,
    "ph.d": 5,
    "master": 4,
    "mtech": 4,
    "m.tech": 4,
    "msc": 4,
    "mba": 4,
    "bachelor": 3,
    "btech": 3,
    "b.tech": 3,
    "bsc": 3,
    "diploma": 2,
}


@dataclass
class MatchResult:
    overall_score: float = 0.0
    semantic_score: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    keyword_score: float = 0.0
    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    additional_skills: list[str] = field(default_factory=list)
    breakdown: dict = field(default_factory=dict)


def cosine_similarity(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def _semantic_score(job_vec: list[float] | None, resume_vec: list[float] | None) -> float:
    if not job_vec or not resume_vec:
        return 0.0
    sim = cosine_similarity(job_vec, resume_vec)
    # Map cosine [-1, 1] -> [0, 100], clamped.
    return max(0.0, min(100.0, (sim + 1) / 2 * 100))


def _skill_score(job_skills: list[str], candidate_skills: list[str]) -> tuple[float, list, list, list]:
    job_set = {s.lower() for s in job_skills}
    cand_set = {s.lower() for s in candidate_skills}
    if not job_set:
        return 100.0, sorted(cand_set), [], sorted(cand_set)
    matched = sorted(job_set & cand_set)
    missing = sorted(job_set - cand_set)
    additional = sorted(cand_set - job_set)
    score = len(matched) / len(job_set) * 100
    return score, matched, missing, additional


def _experience_score(required_years: float, candidate_years: float) -> float:
    if required_years <= 0:
        return 100.0 if candidate_years > 0 else 60.0
    ratio = candidate_years / required_years
    return float(min(100.0, ratio * 100))


def _education_level(text: str) -> int:
    lowered = text.lower()
    best = 0
    for key, level in EDUCATION_LEVELS.items():
        if key in lowered:
            best = max(best, level)
    return best


def _education_score(job_text: str, candidate_education_text: str) -> float:
    required = _education_level(job_text)
    candidate = _education_level(candidate_education_text)
    if required == 0:
        return 100.0 if candidate > 0 else 70.0
    if candidate >= required:
        return 100.0
    return float(max(0.0, candidate / required * 100))


def _keyword_score(job_text: str, resume_text: str) -> float:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", job_text.lower())
    stop = {
        "the", "and", "for", "with", "you", "our", "are", "will", "this", "that",
        "have", "from", "your", "who", "all", "job", "role", "work", "team",
    }
    keywords = {t for t in tokens if t not in stop}
    if not keywords:
        return 0.0
    resume_lower = resume_text.lower()
    hits = sum(1 for k in keywords if k in resume_lower)
    return float(min(100.0, hits / len(keywords) * 100))


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")


def strip_html(text: str | None) -> str:
    """Remove HTML tags (job fields may contain rich-text markup) and collapse
    whitespace, so embeddings and keyword matching operate on clean text."""
    if not text:
        return ""
    no_tags = _TAG_RE.sub(" ", text)
    no_tags = (
        no_tags.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    return _WS_RE.sub(" ", no_tags).strip()


def build_job_text(job) -> str:
    parts = [
        job.title or "",
        job.department or "",
        strip_html(job.description),
        strip_html(job.responsibilities),
        strip_html(job.qualifications),
        " ".join(job.skills or []),
    ]
    return "\n".join(p for p in parts if p)


def build_resume_text(candidate, resume_text: str) -> str:
    parts = [
        candidate.name or "",
        candidate.designation or "",
        " ".join(candidate.skills or []),
        resume_text or "",
    ]
    return "\n".join(p for p in parts if p)


def compute_match(
    *,
    job,
    candidate,
    resume_text: str,
    job_vector: list[float] | None,
    resume_vector: list[float] | None,
) -> MatchResult:
    job_text = build_job_text(job)
    job_skills = job.skills or extract_skills_from_text(job_text)
    candidate_skills = candidate.skills or []

    semantic = _semantic_score(job_vector, resume_vector)
    skill, matched, missing, additional = _skill_score(job_skills, candidate_skills)
    experience = _experience_score(
        float(job.min_experience_years or 0), float(candidate.total_experience_years or 0)
    )
    education_text = " ".join(e.get("detail", "") for e in (candidate.education or []))
    education = _education_score(job_text + " " + strip_html(job.qualifications), education_text)
    keyword = _keyword_score(job_text, resume_text)

    overall = (
        WEIGHTS["semantic"] * semantic
        + WEIGHTS["skills"] * skill
        + WEIGHTS["experience"] * experience
        + WEIGHTS["education"] * education
        + WEIGHTS["keyword"] * keyword
    )

    breakdown = {
        "weights": WEIGHTS,
        "components": {
            "semantic": round(semantic, 2),
            "skills": round(skill, 2),
            "experience": round(experience, 2),
            "education": round(education, 2),
            "keyword": round(keyword, 2),
        },
        "weighted": {
            "semantic": round(WEIGHTS["semantic"] * semantic, 2),
            "skills": round(WEIGHTS["skills"] * skill, 2),
            "experience": round(WEIGHTS["experience"] * experience, 2),
            "education": round(WEIGHTS["education"] * education, 2),
            "keyword": round(WEIGHTS["keyword"] * keyword, 2),
        },
    }

    return MatchResult(
        overall_score=round(overall, 2),
        semantic_score=round(semantic, 2),
        skill_score=round(skill, 2),
        experience_score=round(experience, 2),
        education_score=round(education, 2),
        keyword_score=round(keyword, 2),
        matching_skills=matched,
        missing_skills=missing,
        additional_skills=additional,
        breakdown=breakdown,
    )
