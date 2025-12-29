"""End-to-end screening pipeline test (requires DB; uses the local AI provider).

Exercises parse -> embed -> score -> persist, covering the screening service,
embedding repository (pgvector) and candidate repository.
"""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import pytest

from app.models.candidate_score import CandidateScore
from app.models.job import Job
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.repositories import candidate_repo
from app.services import screening

RESUME_TEXT = """Maria Garcia
maria.garcia@example.com | +1 408 555 0142 | Austin, TX
Senior Backend Engineer

EXPERIENCE
Senior Backend Engineer at Cloudscale Inc
- Built Python and FastAPI services on PostgreSQL and Docker
7 years experience

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS

EDUCATION
Master of Science in Computer Science
"""


@pytest.fixture
def seeded_resume(db_session, tmp_path):
    user = User(
        email=f"e2e_{uuid.uuid4().hex[:8]}@example.com",
        full_name="E2E Recruiter",
        hashed_password="x",
    )
    db_session.add(user)
    db_session.commit()

    job = Job(
        owner_id=user.id,
        title="Senior Backend Engineer",
        description="Build scalable Python APIs",
        skills=["python", "fastapi", "postgresql", "docker"],
        min_experience_years=5,
    )
    db_session.add(job)
    db_session.commit()

    # Persist a real file so parse_resume_file can read it.
    f = Path(tempfile.mkstemp(suffix=".txt")[1])
    f.write_text(RESUME_TEXT, encoding="utf-8")
    resume = Resume(
        job_id=job.id,
        uploader_id=user.id,
        status=ResumeStatus.uploaded,
        original_filename="maria_garcia.txt",
        stored_path=str(f),
        content_type="text/plain",
        file_size=len(RESUME_TEXT),
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume


def test_process_resume_end_to_end(db_session, seeded_resume):
    screening.process_resume(db_session, seeded_resume.id)
    db_session.refresh(seeded_resume)

    assert seeded_resume.status == ResumeStatus.scored

    candidate = candidate_repo.get_by_resume(db_session, seeded_resume.id)
    assert candidate is not None
    assert candidate.email == "maria.garcia@example.com"
    assert "python" in candidate.skills

    score = (
        db_session.query(CandidateScore)
        .filter(CandidateScore.candidate_id == candidate.id)
        .one()
    )
    assert 0 <= score.overall_score <= 100
    assert score.skill_score > 0

    # Ranked listing should now include the scored candidate.
    total, rows = candidate_repo.list_ranked(db_session, job_id=seeded_resume.job_id)
    assert total >= 1
