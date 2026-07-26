"""Integration tests for the upload pipeline: create -> async processing ->
status polling -> list/get/delete, plus validation, RBAC, and multi-tenant
isolation.

Celery runs "eagerly" (synchronously, in-process) via the `celery_eager`
fixture, so these tests exercise the real extraction code without needing
a running Redis broker or worker.
"""
import json
from pathlib import Path

from tests.conftest import auth_header

SAMPLE_CSV = b"name,department,hours\nAda,Engineering,40\nMax,Sales,35\n"


def _upload_csv(client, token, filename="tasks.csv", content=SAMPLE_CSV):
    return client.post(
        "/api/v1/uploads",
        files={"file": (filename, content, "text/csv")},
        headers=auth_header(token),
    )


def test_upload_csv_is_processed_successfully(client, celery_eager, register_company):
    tokens, _ = register_company()
    token = tokens["access_token"]

    response = _upload_csv(client, token)
    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "tasks.csv"
    assert body["file_type"] == "csv"
    # Celery ran eagerly during the request's aftermath (task queued via .delay()
    # inside the request); by the time we check status it should be done.
    upload_id = body["id"]

    status_response = client.get(f"/api/v1/uploads/{upload_id}/status", headers=auth_header(token))
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "done"

    detail = client.get(f"/api/v1/uploads/{upload_id}", headers=auth_header(token))
    assert detail.status_code == 200
    assert detail.json()["error_message"] is None


def test_extracted_json_is_written_to_disk(client, celery_eager, register_company):
    tokens, _ = register_company()
    token = tokens["access_token"]

    response = _upload_csv(client, token)
    upload_id = response.json()["id"]

    detail = client.get(f"/api/v1/uploads/{upload_id}", headers=auth_header(token)).json()
    assert detail["status"] == "done"

    # Fetch the raw DB row via the service isn't exposed over the API, but we
    # can confirm the extracted preview shape indirectly through row/column
    # counts by re-reading the file from the known storage layout.
    from app.core.config import get_settings

    settings = get_settings()
    company_dir = Path(settings.upload_storage_path) / detail["company_id"]
    json_files = list(company_dir.glob(f"{upload_id}.json"))
    assert len(json_files) == 1

    extracted = json.loads(json_files[0].read_text())
    assert extracted["row_count"] == 2
    assert extracted["column_count"] == 3
    assert "department" in extracted["columns"]


def test_upload_rejects_unsupported_extension(client, register_company):
    tokens, _ = register_company()
    response = client.post(
        "/api/v1/uploads",
        files={"file": ("malware.exe", b"binary", "application/octet-stream")},
        headers=auth_header(tokens["access_token"]),
    )
    assert response.status_code == 415


def test_upload_rejects_oversized_file(client, register_company, monkeypatch):
    tokens, _ = register_company()
    monkeypatch.setattr("app.services.upload_service.settings.max_upload_size_mb", 0)

    response = _upload_csv(client, tokens["access_token"])
    assert response.status_code == 413


def test_upload_requires_authentication(client):
    response = client.post("/api/v1/uploads", files={"file": ("tasks.csv", SAMPLE_CSV, "text/csv")})
    assert response.status_code == 401


def test_list_uploads_only_shows_own_company(client, celery_eager, register_company):
    tokens_a, _ = register_company(company_name="Company A", email="admin-a@up.test")
    tokens_b, _ = register_company(company_name="Company B", email="admin-b@up.test")

    _upload_csv(client, tokens_a["access_token"], filename="a.csv")

    list_a = client.get("/api/v1/uploads", headers=auth_header(tokens_a["access_token"]))
    assert len(list_a.json()) == 1

    list_b = client.get("/api/v1/uploads", headers=auth_header(tokens_b["access_token"]))
    assert list_b.json() == []


def test_get_upload_from_another_company_is_not_found(client, celery_eager, register_company):
    tokens_a, _ = register_company(company_name="Company A", email="admin-a2@up.test")
    tokens_b, _ = register_company(company_name="Company B", email="admin-b2@up.test")

    upload_id = _upload_csv(client, tokens_a["access_token"]).json()["id"]

    response = client.get(f"/api/v1/uploads/{upload_id}", headers=auth_header(tokens_b["access_token"]))
    assert response.status_code == 404


def test_owner_can_delete_own_upload(client, celery_eager, register_company):
    tokens, _ = register_company()
    upload_id = _upload_csv(client, tokens["access_token"]).json()["id"]

    response = client.delete(f"/api/v1/uploads/{upload_id}", headers=auth_header(tokens["access_token"]))
    assert response.status_code == 204

    follow_up = client.get(f"/api/v1/uploads/{upload_id}", headers=auth_header(tokens["access_token"]))
    assert follow_up.status_code == 404


def test_employee_cannot_delete_someone_elses_upload(client, celery_eager, register_company):
    tokens, _ = register_company()
    admin_token = tokens["access_token"]

    # Admin invites an employee, and the admin (not the employee) uploads a file.
    client.post(
        "/api/v1/users",
        json={
            "full_name": "Eddie Employee",
            "email": "employee@up.test",
            "password": "StrongPass123",
            "role": "employee",
        },
        headers=auth_header(admin_token),
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "employee@up.test", "password": "StrongPass123"}
    )
    employee_token = login.json()["access_token"]

    upload_id = _upload_csv(client, admin_token).json()["id"]

    response = client.delete(f"/api/v1/uploads/{upload_id}", headers=auth_header(employee_token))
    assert response.status_code == 403


def test_admin_can_delete_another_users_upload(client, celery_eager, register_company):
    tokens, _ = register_company()
    admin_token = tokens["access_token"]

    client.post(
        "/api/v1/users",
        json={
            "full_name": "Eddie Employee",
            "email": "employee2@up.test",
            "password": "StrongPass123",
            "role": "employee",
        },
        headers=auth_header(admin_token),
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "employee2@up.test", "password": "StrongPass123"}
    )
    employee_token = login.json()["access_token"]

    upload_id = _upload_csv(client, employee_token).json()["id"]

    response = client.delete(f"/api/v1/uploads/{upload_id}", headers=auth_header(admin_token))
    assert response.status_code == 204
