"""Multi-tenant isolation: company_id always comes from the resolved user's
own record, never from client input — one tenant can never read or act on
another tenant's data."""


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_user_list_only_shows_own_company(client, register_company):
    tokens_a, _ = register_company(company_name="Company A", email="admin-a@test.com")
    tokens_b, _ = register_company(company_name="Company B", email="admin-b@test.com")

    # Company A invites a teammate.
    client.post(
        "/api/v1/users",
        json={
            "full_name": "A Teammate",
            "email": "teammate-a@test.com",
            "password": "StrongPass123",
            "role": "employee",
        },
        headers=_auth_header(tokens_a["access_token"]),
    )

    list_a = client.get("/api/v1/users", headers=_auth_header(tokens_a["access_token"]))
    emails_a = {u["email"] for u in list_a.json()}
    assert "admin-a@test.com" in emails_a
    assert "teammate-a@test.com" in emails_a
    assert "admin-b@test.com" not in emails_a

    list_b = client.get("/api/v1/users", headers=_auth_header(tokens_b["access_token"]))
    emails_b = {u["email"] for u in list_b.json()}
    assert emails_b == {"admin-b@test.com"}


def test_invited_user_belongs_to_inviter_company_not_a_client_supplied_one(client, register_company):
    """UserInvite has no company_id field — even if a client tried to smuggle one
    in the JSON body, Pydantic would ignore it since it's not part of the schema."""
    tokens_a, _ = register_company(company_name="Company A", email="admin-a2@test.com")

    response = client.post(
        "/api/v1/users",
        json={
            "full_name": "Sneaky",
            "email": "sneaky@test.com",
            "password": "StrongPass123",
            "role": "employee",
            "company_id": "11111111-1111-1111-1111-111111111111",
        },
        headers=_auth_header(tokens_a["access_token"]),
    )
    assert response.status_code == 201

    me_a = client.get("/api/v1/auth/me", headers=_auth_header(tokens_a["access_token"]))
    admin_company_id = me_a.json()["company_id"]

    users_a = client.get("/api/v1/users", headers=_auth_header(tokens_a["access_token"])).json()
    sneaky_user = next(u for u in users_a if u["email"] == "sneaky@test.com")
    assert sneaky_user["company_id"] == admin_company_id
