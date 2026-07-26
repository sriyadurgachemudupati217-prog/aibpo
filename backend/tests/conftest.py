"""Shared test fixtures.

Uses an in-memory SQLite DB (via the cross-dialect GUID type in
app.db.base) so the full auth stack can be tested without a running
Postgres instance. Each test gets a fresh schema.
"""
import os
import tempfile

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("UPLOAD_STORAGE_PATH", tempfile.mkdtemp(prefix="aibpo_uploads_test_"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import *  # noqa: F401,F403 registers all models on Base.metadata


@pytest.fixture()
def db_session(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Phase 2: Celery tasks are run "eagerly" (synchronously, in-process)
    # during tests — see the `celery_eager` fixture — and open their own DB
    # session via `app.db.session.SessionLocal`. Patch that module-level
    # session factory to point at this same test engine, so a task
    # triggered inside a test sees the rows the test just committed.
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSessionLocal)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def _get_db_override():
        # Phase 2: a Celery task run eagerly commits via its own session on
        # the same underlying connection. Expiring here forces this shared
        # session to re-SELECT (rather than serve stale cached attributes)
        # on the next access, so status updates from the task are visible.
        db_session.expire_all()
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def register_company(client):
    """Registers a company + admin, returns (tokens, credentials)."""

    def _register(company_name="Acme Inc", email="admin@acme.test", password="StrongPass123"):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": company_name,
                "full_name": "Ada Admin",
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 201, response.text
        return response.json(), {"email": email, "password": password}

    return _register


@pytest.fixture()
def celery_eager():
    """Runs Celery tasks synchronously in-process (Phase 2), so upload
    processing tests don't need a running Redis broker or worker."""
    from app.workers.celery_app import celery_app

    original_always_eager = celery_app.conf.task_always_eager
    original_eager_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    try:
        yield
    finally:
        celery_app.conf.task_always_eager = original_always_eager
        celery_app.conf.task_eager_propagates = original_eager_propagates


def auth_header(access_token: str) -> dict[str, str]:
    """Shared helper: builds an Authorization header from an access token."""
    return {"Authorization": f"Bearer {access_token}"}
