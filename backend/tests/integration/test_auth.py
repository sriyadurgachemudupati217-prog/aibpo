"""Integration tests for the auth flow: register -> login -> refresh -> logout,
plus password reset and input validation."""


def test_register_creates_company_and_admin(client, register_company):
    tokens, _ = register_company()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["role"] == "admin"


def test_register_rejects_duplicate_email(client, register_company):
    register_company(email="dup@acme.test")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Other Co",
            "full_name": "Someone Else",
            "email": "dup@acme.test",
            "password": "StrongPass123",
        },
    )
    assert response.status_code == 409


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Acme Inc",
            "full_name": "Ada Admin",
            "email": "weak@acme.test",
            "password": "weak",
        },
    )
    assert response.status_code == 422


def test_login_with_correct_credentials(client, register_company):
    _, creds = register_company()
    response = client.post("/api/v1/auth/login", json=creds)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_is_rejected(client, register_company):
    _, creds = register_company()
    response = client.post(
        "/api/v1/auth/login", json={"email": creds["email"], "password": "WrongPass123"}
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_rotates_token_and_invalidates_old_one(client, register_company):
    tokens, _ = register_company()

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # Reusing the original (now-rotated) refresh token must fail.
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert replay.status_code == 401

    # The new refresh token works.
    second_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})
    assert second_refresh.status_code == 200


def test_logout_revokes_refresh_token(client, register_company):
    tokens, _ = register_company()

    logout_resp = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout_resp.status_code == 200

    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_resp.status_code == 401


def test_password_reset_flow(client, register_company, db_session):
    _, creds = register_company()

    # Request always returns 200 with a generic message, whether or not the email exists.
    unknown = client.post("/api/v1/auth/password-reset/request", json={"email": "nobody@acme.test"})
    assert unknown.status_code == 200

    # Simulate the service call directly to get the raw token (Phase 1 has no email
    # provider wired up — the router only logs it).
    from app.services.auth_service import AuthService

    raw_token = AuthService(db_session).request_password_reset(creds["email"])
    assert raw_token is not None

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "BrandNewPass123"},
    )
    assert confirm.status_code == 200

    old_login = client.post("/api/v1/auth/login", json=creds)
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login", json={"email": creds["email"], "password": "BrandNewPass123"}
    )
    assert new_login.status_code == 200


def test_password_reset_token_is_single_use(client, register_company, db_session):
    _, creds = register_company()

    from app.services.auth_service import AuthService

    raw_token = AuthService(db_session).request_password_reset(creds["email"])

    first = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "FirstNewPass123"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "SecondNewPass123"},
    )
    assert second.status_code == 401
