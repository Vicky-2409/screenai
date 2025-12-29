"""Integration tests for resume upload, candidates, analytics, reports, admin.

These run against the CI Postgres + Redis services. Scoring is asynchronous
(Celery), so these tests assert endpoint behaviour up to enqueue, plus the
synchronous pieces (file persistence, analytics shape, reports, authz).
"""
from __future__ import annotations


def _auth(client, unique_email):
    reg = client.post(
        "/api/auth/register",
        json={"email": unique_email, "full_name": "Recruiter", "password": "supersecret1"},
    )
    assert reg.status_code == 201, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _make_job(client, headers):
    res = client.post(
        "/api/jobs",
        headers=headers,
        json={
            "title": "Backend Engineer",
            "description": "<p>Build <b>APIs</b></p>",
            "skills": ["python", "fastapi"],
            "min_experience_years": 3,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_upload_list_and_download_resume(client, unique_email):
    headers = _auth(client, unique_email)
    job_id = _make_job(client, headers)

    files = {"files": ("resume.txt", b"Jane Doe\njane@example.com\nPython FastAPI 5 years", "text/plain")}
    up = client.post(f"/api/jobs/{job_id}/upload", headers=headers, files=files)
    assert up.status_code == 201, up.text
    uploaded = up.json()["uploaded"]
    assert len(uploaded) == 1
    resume_id = uploaded[0]["id"]

    # List resumes for the job
    listed = client.get(f"/api/jobs/{job_id}/resumes", headers=headers)
    assert listed.status_code == 200
    assert any(r["id"] == resume_id for r in listed.json())

    # Progress endpoint
    prog = client.get(f"/api/jobs/{job_id}/progress", headers=headers)
    assert prog.status_code == 200
    assert prog.json()["total"] == 1

    # File is persisted synchronously and downloadable by the owner
    file_res = client.get(f"/api/resumes/{resume_id}/file", headers=headers)
    assert file_res.status_code == 200
    assert b"Jane Doe" in file_res.content


def test_resume_file_forbidden_for_non_owner(client, unique_email):
    owner_headers = _auth(client, unique_email)
    job_id = _make_job(client, owner_headers)
    files = {"files": ("r.txt", b"hello world", "text/plain")}
    up = client.post(f"/api/jobs/{job_id}/upload", headers=owner_headers, files=files)
    resume_id = up.json()["uploaded"][0]["id"]

    other = _auth(client, f"other_{unique_email}")
    res = client.get(f"/api/resumes/{resume_id}/file", headers=other)
    assert res.status_code == 403


def test_candidates_list_empty_initially(client, unique_email):
    headers = _auth(client, unique_email)
    job_id = _make_job(client, headers)
    res = client.get(f"/api/jobs/{job_id}/candidates", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_analytics_dashboard_shape(client, unique_email):
    headers = _auth(client, unique_email)
    _make_job(client, headers)
    res = client.get("/api/analytics/dashboard", headers=headers)
    assert res.status_code == 200
    body = res.json()
    for key in (
        "stats",
        "skill_distribution",
        "score_distribution",
        "resume_sources",
        "job_performance",
        "hiring_funnel",
    ):
        assert key in body


def test_reports_csv_and_pdf(client, unique_email):
    headers = _auth(client, unique_email)
    job_id = _make_job(client, headers)

    csv_res = client.get(f"/api/reports/{job_id}/csv", headers=headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]

    pdf_res = client.get(f"/api/reports/{job_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.content[:4] == b"%PDF"


def test_admin_endpoints_require_admin(client, unique_email):
    # The very first registered user becomes admin, so register a throwaway
    # first to guarantee the account under test is a (non-admin) recruiter.
    _auth(client, f"first_{unique_email}")
    headers = _auth(client, unique_email)
    assert client.get("/api/admin/stats", headers=headers).status_code == 403
    assert client.get("/api/admin/storage", headers=headers).status_code == 403


def test_notifications_listing(client, unique_email):
    headers = _auth(client, unique_email)
    res = client.get("/api/notifications", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
