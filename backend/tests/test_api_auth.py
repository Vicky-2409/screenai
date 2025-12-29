"""Integration tests for the authentication + jobs flow (requires DB)."""
from __future__ import annotations


def test_register_login_refresh_me(client, unique_email):
    # Register
    res = client.post(
        "/api/auth/register",
        json={"email": unique_email, "full_name": "Test User", "password": "supersecret1"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == unique_email

    access = body["access_token"]
    refresh = body["refresh_token"]

    # /me with bearer token
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == unique_email

    # Refresh rotation
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    # Old refresh token is now revoked
    reused = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert reused.status_code == 401


def test_login_wrong_password(client, unique_email):
    client.post(
        "/api/auth/register",
        json={"email": unique_email, "full_name": "Test User", "password": "supersecret1"},
    )
    res = client.post("/api/auth/login", json={"email": unique_email, "password": "wrong"})
    assert res.status_code == 401


def test_jobs_crud_requires_auth_and_works(client, unique_email):
    reg = client.post(
        "/api/auth/register",
        json={"email": unique_email, "full_name": "Recruiter", "password": "supersecret1"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Unauthenticated create is rejected
    assert client.post("/api/jobs", json={"title": "X"}).status_code == 401

    # Create
    created = client.post(
        "/api/jobs",
        headers=headers,
        json={"title": "Backend Engineer", "skills": ["python", "fastapi"]},
    )
    assert created.status_code == 201, created.text
    job_id = created.json()["id"]

    # List
    listed = client.get("/api/jobs", headers=headers)
    assert listed.status_code == 200
    assert any(j["id"] == job_id for j in listed.json())

    # Update
    updated = client.put(f"/api/jobs/{job_id}", headers=headers, json={"title": "Senior Backend Engineer"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "Senior Backend Engineer"

    # Delete
    assert client.delete(f"/api/jobs/{job_id}", headers=headers).status_code == 204
