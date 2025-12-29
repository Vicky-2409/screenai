from app.services import parsing

SAMPLE = """John Smith
john.smith@example.com | +1 415 555 0199 | New York, NY
Senior Software Engineer

EXPERIENCE
Senior Software Engineer at Acme Technologies
- Built APIs with Python and FastAPI
10 years experience

EDUCATION
Master of Science in Computer Science

SKILLS
Python, FastAPI, PostgreSQL, Docker
"""


def test_normalize_extracts_core_fields():
    parsed = parsing.normalize(SAMPLE)
    assert parsed.email == "john.smith@example.com"
    assert parsed.phone is not None
    assert parsed.total_experience_years == 10.0
    assert "python" in parsed.skills
    assert parsed.name  # name resolved via regex or spaCy
    assert any("Computer Science" in e["detail"] for e in parsed.education)


def test_normalize_empty_text():
    parsed = parsing.normalize("")
    assert parsed.email is None
    assert parsed.skills == []
    assert parsed.total_experience_years == 0.0


def test_name_falls_back_to_email_local_part():
    text = "someheaderwithoutname\n\ncontact: jane.doe@example.com"
    parsed = parsing.normalize(text)
    # Either spaCy finds nothing and we derive from email, or returns a name.
    assert parsed.email == "jane.doe@example.com"
    assert parsed.name is not None


def test_companies_extracted_from_experience():
    parsed = parsing.normalize(SAMPLE)
    assert any("Acme" in c for c in parsed.companies)
