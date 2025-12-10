"""A pragmatic skill taxonomy used for normalization and matching.

This is intentionally a curated, extensible list rather than an exhaustive
ontology. It powers skill extraction, normalization, and gap analysis.
"""
from __future__ import annotations

import re

# Canonical skill -> set of aliases (all lowercase).
SKILL_ALIASES: dict[str, set[str]] = {
    "python": {"python", "py", "python3"},
    "javascript": {"javascript", "js", "ecmascript"},
    "typescript": {"typescript", "ts"},
    "java": {"java"},
    "c#": {"c#", "csharp", "c sharp", ".net c#"},
    "c++": {"c++", "cpp"},
    "go": {"golang", "go"},
    "rust": {"rust"},
    "ruby": {"ruby"},
    "php": {"php"},
    "react": {"react", "react.js", "reactjs"},
    "react native": {"react native"},
    "redux": {"redux"},
    "angular": {"angular", "angularjs"},
    "vue": {"vue", "vue.js", "vuejs"},
    "next.js": {"next.js", "nextjs", "next"},
    "node.js": {"node.js", "nodejs", "node"},
    "express": {"express", "express.js"},
    "fastapi": {"fastapi"},
    "django": {"django"},
    "flask": {"flask"},
    "spring": {"spring", "spring boot", "springboot"},
    ".net": {".net", "dotnet", "asp.net", "asp.net core"},
    "sql": {"sql"},
    "postgresql": {"postgresql", "postgres", "psql"},
    "mysql": {"mysql"},
    "mongodb": {"mongodb", "mongo"},
    "redis": {"redis"},
    "elasticsearch": {"elasticsearch", "elastic search", "es"},
    "pgvector": {"pgvector"},
    "docker": {"docker"},
    "kubernetes": {"kubernetes", "k8s"},
    "aws": {"aws", "amazon web services"},
    "azure": {"azure", "microsoft azure"},
    "gcp": {"gcp", "google cloud", "google cloud platform"},
    "terraform": {"terraform"},
    "ci/cd": {"ci/cd", "cicd", "ci cd"},
    "github actions": {"github actions"},
    "jenkins": {"jenkins"},
    "graphql": {"graphql"},
    "rest": {"rest", "rest api", "restful"},
    "grpc": {"grpc"},
    "kafka": {"kafka", "apache kafka"},
    "rabbitmq": {"rabbitmq"},
    "celery": {"celery"},
    "spark": {"spark", "apache spark", "pyspark"},
    "pandas": {"pandas"},
    "numpy": {"numpy"},
    "pytorch": {"pytorch", "torch"},
    "tensorflow": {"tensorflow", "tf"},
    "scikit-learn": {"scikit-learn", "sklearn", "scikit learn"},
    "nlp": {"nlp", "natural language processing"},
    "machine learning": {"machine learning", "ml"},
    "deep learning": {"deep learning"},
    "langchain": {"langchain"},
    "openai": {"openai", "gpt", "llm", "large language models"},
    "git": {"git"},
    "linux": {"linux", "unix"},
    "html": {"html", "html5"},
    "css": {"css", "css3"},
    "tailwind": {"tailwind", "tailwindcss", "tailwind css"},
    "sass": {"sass", "scss"},
    "agile": {"agile", "scrum"},
    "microservices": {"microservices", "micro services"},
}

# Reverse index: alias -> canonical
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in SKILL_ALIASES.items():
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias] = canonical
    _ALIAS_TO_CANONICAL[canonical] = canonical

ALL_ALIASES = sorted(_ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)


def normalize_skill(token: str) -> str | None:
    """Return the canonical skill name for a token, or None if unknown."""
    return _ALIAS_TO_CANONICAL.get(token.strip().lower())


def extract_skills_from_text(text: str) -> list[str]:
    """Extract canonical skills present in free text.

    Uses boundary lookarounds so aliases match regardless of surrounding
    punctuation or whitespace (commas, newlines) while avoiding partial hits
    such as 'go' inside 'google'. Characters valid inside a skill token
    (letters, digits, ``+ # .``) are excluded from the boundaries.
    """
    lowered = text.lower()
    found: set[str] = set()
    for alias in ALL_ALIASES:
        # Boundaries exclude only alphanumerics so punctuation (commas, periods,
        # slashes) acts as a delimiter, while 'go' still won't match 'google'.
        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            found.add(_ALIAS_TO_CANONICAL[alias])
    return sorted(found)
