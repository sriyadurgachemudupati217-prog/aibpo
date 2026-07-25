"""Shared test fixtures.

Uses an in-memory SQLite DB (via the cross-dialect GUID type in
app.db.base) so the full auth stack can be tested without a running
Postgres instance. Each test gets a fresh schema.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

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
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def _get_db_override():
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
