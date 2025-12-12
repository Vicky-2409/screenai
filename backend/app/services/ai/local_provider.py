"""Local, zero-cost AI provider using sentence-transformers and heuristics."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.provider import AnalysisResult

logger = get_logger(__name__)


@lru_cache
def _load_model():
    from sentence_transformers import SentenceTransformer

    logger.info("Loading local embedding model: %s", settings.local_embedding_model)
    return SentenceTransformer(settings.local_embedding_model)


class LocalProvider:
    name = "local"

    def __init__(self) -> None:
        self.model = settings.local_embedding_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = _load_model()
        vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return [v.tolist() for v in vectors]

    def analyze_candidate(self, job_text: str, resume_text: str, context: dict) -> AnalysisResult:
        """Heuristic analysis based on already-computed score context.

        ``context`` carries the structured scoring output so the local provider
        can produce a coherent, recruiter-style narrative without an LLM.
        """
        overall = context.get("overall_score", 0)
        matching = context.get("matching_skills", [])
        missing = context.get("missing_skills", [])
        exp_years = context.get("total_experience_years", 0)
        name = context.get("name") or "The candidate"

        strengths: list[str] = []
        if matching:
            strengths.append(f"Strong match on key skills: {', '.join(matching[:6])}")
        if exp_years >= context.get("min_experience_years", 0) and exp_years > 0:
            strengths.append(f"Has {exp_years:.0f}+ years of relevant experience")
        if context.get("semantic_score", 0) >= 70:
            strengths.append("Resume content is highly semantically aligned with the role")
        if not strengths:
            strengths.append("Some transferable experience present")

        weaknesses: list[str] = []
        if missing:
            weaknesses.append(f"Missing required skills: {', '.join(missing[:6])}")
        if exp_years < context.get("min_experience_years", 0):
            weaknesses.append("Experience below the minimum required for the role")
        if context.get("education_score", 0) < 50:
            weaknesses.append("Education background not clearly aligned with requirements")
        if not weaknesses:
            weaknesses.append("No significant gaps detected")

        if overall >= 80:
            rec = "Strongly recommended - advance to technical round"
        elif overall >= 65:
            rec = "Recommended - worth an initial screening call"
        elif overall >= 50:
            rec = "Maybe - consider if pipeline is thin"
        else:
            rec = "Not recommended for this role"

        summary = (
            f"{name} achieves an overall match of {overall:.0f}%. "
            f"Matched {len(matching)} of the role's key skills"
            + (f" while missing {len(missing)}." if missing else ".")
            + f" Estimated {exp_years:.0f} years of experience."
        )

        questions = [
            f"Can you describe a project where you applied {matching[0]}?"
            if matching
            else "Walk me through a recent project you're proud of.",
            f"How would you ramp up on {missing[0]}?"
            if missing
            else "How do you approach learning new technologies?",
            "Describe a challenging technical problem you solved and your approach.",
            "How do you collaborate with cross-functional teams?",
        ]

        culture_fit = (
            "Communication and collaboration signals should be validated in the interview; "
            "resume content suggests a "
            + ("strong" if overall >= 70 else "moderate")
            + " fit for a fast-paced team."
        )

        return AnalysisResult(
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_skills=missing,
            matching_skills=matching,
            recommendation=rec,
            culture_fit=culture_fit,
            interview_questions=questions,
        )
