from app.services.parsing import normalize

SAMPLE = """John Doe
john.doe@example.com
+1 (555) 123-4567

Senior Software Engineer with 7 years of experience.

Skills
Python, FastAPI, React, PostgreSQL, Docker, AWS

Experience
Software Engineer at Acme Technologies
Backend Developer at Globex Systems

Education
B.Tech in Computer Science

Certifications
AWS Certified Solutions Architect
"""


def test_normalize_extracts_contact_and_skills():
    parsed = normalize(SAMPLE)
    assert parsed.email == "john.doe@example.com"
    assert parsed.phone is not None
    assert parsed.total_experience_years == 7
    assert "python" in parsed.skills
    assert "fastapi" in parsed.skills
    assert parsed.name == "John Doe"


def test_normalize_handles_empty_text():
    parsed = normalize("")
    assert parsed.email is None
    assert parsed.skills == []
    assert parsed.total_experience_years == 0
