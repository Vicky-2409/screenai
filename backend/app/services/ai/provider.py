"""AI provider abstraction.

Exposes a single interface used across the app for:
  * embedding text into vectors (for pgvector semantic search)
  * analyzing a candidate against a job (LLM-style structured output)

Two implementations are selected at runtime based on settings:
  * OpenAIProvider  - uses the OpenAI API (embeddings + chat completion)
  * LocalProvider   - uses sentence-transformers + heuristic analysis so the
                      whole system runs with zero external dependencies/cost.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    summary: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    matching_skills: list[str] = field(default_factory=list)
    recommendation: str = ""
    culture_fit: str = ""
    interview_questions: list[str] = field(default_factory=list)


class AIProvider(Protocol):
    name: str
    model: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def analyze_candidate(self, job_text: str, resume_text: str, context: dict) -> AnalysisResult: ...


@lru_cache
def get_ai_provider() -> AIProvider:
    provider = settings.resolved_ai_provider
    if provider == "openai":
        from app.services.ai.openai_provider import OpenAIProvider

        logger.info("Using OpenAI AI provider")
        return OpenAIProvider()
    from app.services.ai.local_provider import LocalProvider

    logger.info("Using local AI provider (sentence-transformers)")
    return LocalProvider()
