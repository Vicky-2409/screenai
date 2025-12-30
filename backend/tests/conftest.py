"""Shared pytest fixtures.

Integration tests need a reachable Postgres (with pgvector) and Redis. When the
database is unavailable (e.g. a pure unit-test run), the ``client`` fixture is
skipped automatically so unit tests still pass in isolation.
"""
from __future__ import annotations

import os
import tempfile
import uuid

import pytest

# Tests must never write to the production default ("/data/uploads"), which is not
# writable in CI. Point uploads at a writable temp dir before any app import loads
# the settings singleton. An explicit UPLOAD_DIR from the environment still wins.
os.environ.setdefault("UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "ats_test_uploads"))


def _db_available() -> bool:
    try:
        from sqlalchemy import text

        from app.core.database import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


@pytest.fixture(scope="session")
def client():
    if not _db_available():
        pytest.skip("Database not available; skipping integration tests")
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def unique_email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture
def db_session():
    if not _db_available():
        pytest.skip("Database not available; skipping integration tests")
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
