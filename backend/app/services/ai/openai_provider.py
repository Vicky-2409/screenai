"""OpenAI-backed AI provider for embeddings and candidate analysis."""
from __future__ import annotations

import json

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.provider import AnalysisResult

logger = get_logger(__name__)

ANALYSIS_SYSTEM_PROMPT = (
    "You are an expert technical recruiter. Analyze how well a candidate's resume "
    "matches a job description. Respond ONLY with valid JSON matching the requested schema."
)

ANALYSIS_SCHEMA_HINT = {
    "summary": "string - 2-3 sentence candidate summary",
    "strengths": ["string"],
    "weaknesses": ["string"],
    "missing_skills": ["string"],
    "matching_skills": ["string"],
    "recommendation": "string - hiring recommendation",
    "culture_fit": "string - culture fit assessment",
    "interview_questions": ["string - 4 tailored interview questions"],
}


class OpenAIProvider:
    name = "openai"

    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_chat_model
        self.embedding_model = settings.openai_embedding_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        cleaned = [t.replace("\n", " ")[:8000] for t in texts]
        resp = self.client.embeddings.create(model=self.embedding_model, input=cleaned)
        return [d.embedding for d in resp.data]

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=8))
    def analyze_candidate(self, job_text: str, resume_text: str, context: dict) -> AnalysisResult:
        user_prompt = (
            f"JOB DESCRIPTION:\n{job_text[:6000]}\n\n"
            f"CANDIDATE RESUME:\n{resume_text[:8000]}\n\n"
            f"PRE-COMPUTED SCORES (for reference):\n{json.dumps(context, default=str)[:2000]}\n\n"
            f"Return JSON with this shape:\n{json.dumps(ANALYSIS_SCHEMA_HINT)}"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            return AnalysisResult(
                summary=data.get("summary", ""),
                strengths=list(data.get("strengths", [])),
                weaknesses=list(data.get("weaknesses", [])),
                missing_skills=list(data.get("missing_skills", context.get("missing_skills", []))),
                matching_skills=list(data.get("matching_skills", context.get("matching_skills", []))),
                recommendation=data.get("recommendation", ""),
                culture_fit=data.get("culture_fit", ""),
                interview_questions=list(data.get("interview_questions", [])),
            )
        except Exception as exc:  # noqa: BLE001 - fall back gracefully
            logger.warning("OpenAI analysis failed, using heuristic fallback: %s", exc)
            from app.services.ai.local_provider import LocalProvider

            return LocalProvider().analyze_candidate(job_text, resume_text, context)
