"""RBAC tests: only Admin/Manager can invite users; Employee is denied."""


def _login(client, creds):
    resp = client.post("/api/v1/auth/login", json=creds)
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_invite_users(client, register_company):
    tokens, creds = register_company()
    admin_token = tokens["access_token"]

    response = client.post(
        "/api/v1/users",
        json={
            "full_name": "Manny Manager",
            "email": "manager@acme.test",
            "password": "StrongPass123",
            "role": "manager",
        },
        headers=_auth_header(admin_token),
    )
    assert response.status_code == 201
    assert response.json()["role"] == "manager"


def test_manager_can_invite_users(client, register_company):
    tokens, _ = register_company()
    admin_token = tokens["access_token"]

    client.post(
        "/api/v1/users",
        json={
            "full_name": "Manny Manager",
            "email": "manager@acme.test",
            "password": "StrongPass123",
            "role": "manager",
        },
        headers=_auth_header(admin_token),
    )
    manager_token = _login(client, {"email": "manager@acme.test", "password": "StrongPass123"})

    response = client.post(
        "/api/v1/users",
        json={
            "full_name": "Eddie Employee",
            "email": "employee@acme.test",
            "password": "StrongPass123",
            "role": "employee",
        },
        headers=_auth_header(manager_token),
    )
    assert response.status_code == 201


def test_employee_cannot_invite_users(client, register_company):
    tokens, admin_creds = register_company()
    admin_token = tokens["access_token"]

    client.post(
        "/api/v1/users",
        json={
            "full_name": "Eddie Employee",
            "email": "employee@acme.test",
            "password": "StrongPass123",
            "role": "employee",
        },
        headers=_auth_header(admin_token),
    )
    employee_token = _login(client, {"email": "employee@acme.test", "password": "StrongPass123"})

    response = client.post(
        "/api/v1/users",
        json={
            "full_name": "Another Person",
            "email": "another@acme.test",
            "password": "StrongPass123",
            "role": "employee",
        },
        headers=_auth_header(employee_token),
    )
    assert response.status_code == 403


def test_unauthenticated_cannot_invite_users(client):
    response = client.post(
        "/api/v1/users",
        json={
            "full_name": "Nobody",
            "email": "nobody@acme.test",
            "password": "StrongPass123",
            "role": "employee",
        },
    )
    assert response.status_code == 401
