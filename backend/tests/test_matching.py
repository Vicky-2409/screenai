from types import SimpleNamespace

from app.services import matching


def _job():
    return SimpleNamespace(
        title="Backend Engineer",
        department="Engineering",
        description="Build scalable APIs with Python and FastAPI.",
        responsibilities="Design REST APIs",
        qualifications="Bachelor degree in CS",
        skills=["python", "fastapi", "postgresql", "docker"],
        min_experience_years=5,
    )


def _candidate(skills, years):
    return SimpleNamespace(
        name="Jane",
        designation="Engineer",
        skills=skills,
        total_experience_years=years,
        education=[{"detail": "B.Tech Computer Science"}],
    )


def test_cosine_similarity_identical():
    assert matching.cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0


def test_compute_match_high_overlap():
    job = _job()
    cand = _candidate(["python", "fastapi", "postgresql", "docker"], 6)
    result = matching.compute_match(
        job=job,
        candidate=cand,
        resume_text="Python FastAPI PostgreSQL Docker backend engineer with 6 years",
        job_vector=[1.0, 0.0, 0.0],
        resume_vector=[1.0, 0.0, 0.0],
    )
    assert result.skill_score == 100.0
    assert result.experience_score == 100.0
    assert not result.missing_skills
    assert result.overall_score > 80


def test_compute_match_missing_skills():
    job = _job()
    cand = _candidate(["python"], 2)
    result = matching.compute_match(
        job=job,
        candidate=cand,
        resume_text="Python developer",
        job_vector=[1.0, 0.0, 0.0],
        resume_vector=[0.0, 1.0, 0.0],
    )
    assert "fastapi" in result.missing_skills
    assert result.experience_score < 100
    assert result.overall_score < 80


def test_weights_sum_to_one():
    assert abs(sum(matching.WEIGHTS.values()) - 1.0) < 1e-9
