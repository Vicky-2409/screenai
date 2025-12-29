from app.services.skills_db import extract_skills_from_text, normalize_skill


def test_normalize_skill_aliases():
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("postgres") == "postgresql"
    assert normalize_skill("totally-unknown-skill") is None


def test_extract_skills_from_text():
    text = "Experienced Python developer skilled in FastAPI, React and PostgreSQL. Uses Docker."
    skills = extract_skills_from_text(text)
    assert "python" in skills
    assert "fastapi" in skills
    assert "react" in skills
    assert "postgresql" in skills
    assert "docker" in skills
