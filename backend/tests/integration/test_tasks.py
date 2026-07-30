"""Integration tests for Phase 3: task-history ingestion (CSV -> Employee/Task
rows via the Celery pipeline) and the four analysis endpoints plus delay
prediction.

Celery runs eagerly (see `celery_eager` fixture) so ingestion completes
synchronously within the upload request's test.
"""
from tests.conftest import auth_header

TASK_HISTORY_CSV = b"""employee,department,task_name,status,due_at,estimated_hours,actual_hours
Ada,Engineering,Data entry,not_started,2027-01-01,20,
Ada,Engineering,Data entry,not_started,2027-01-01,20,
Ada,Engineering,Data entry,not_started,2027-01-01,20,
Ada,Engineering,Data entry,not_started,2027-01-01,20,
Ada,Engineering,Design review,not_started,2027-01-01,15,
Ada,Engineering,Sprint planning,not_started,2027-01-01,15,
Ada,Engineering,Fix bug,blocked,2027-01-01,10,
Ada,Engineering,Legacy migration,not_started,2020-01-01,8,
Max,Engineering,Standup notes,not_started,2027-01-01,5,
"""


def _upload_task_history(client, token):
    return client.post(
        "/api/v1/uploads",
        files={"file": ("tasks.csv", TASK_HISTORY_CSV, "text/csv")},
        data={"category": "task_history"},
        headers=auth_header(token),
    )


def test_upload_with_task_history_category_ingests_tasks(client, celery_eager, register_company):
    tokens, _ = register_company()
    token = tokens["access_token"]

    upload_response = _upload_task_history(client, token)
    assert upload_response.status_code == 201
    assert upload_response.json()["category"] == "task_history"

    tasks_response = client.get("/api/v1/tasks", headers=auth_header(token))
    assert tasks_response.status_code == 200
    tasks = tasks_response.json()
    assert len(tasks) == 9


def test_task_list_is_isolated_per_company(client, celery_eager, register_company):
    tokens_a, _ = register_company(company_name="Company A", email="admin-a@task.test")
    tokens_b, _ = register_company(company_name="Company B", email="admin-b@task.test")

    _upload_task_history(client, tokens_a["access_token"])

    tasks_a = client.get("/api/v1/tasks", headers=auth_header(tokens_a["access_token"])).json()
    tasks_b = client.get("/api/v1/tasks", headers=auth_header(tokens_b["access_token"])).json()
    assert len(tasks_a) == 9
    assert len(tasks_b) == 0


def test_workload_analysis_flags_overloaded_and_underloaded(client, celery_eager, register_company):
    tokens, _ = register_company()
    token = tokens["access_token"]
    _upload_task_history(client, token)

    response = client.get("/api/v1/tasks/analysis", headers=auth_header(token))
    assert response.status_code == 200
    body = response.json()

    by_name = {e["display_name"]: e for e in body["employees"]}
    assert by_name["Ada"]["flag"] == "overloaded"
    assert by_name["Max"]["flag"] == "underloaded"


def test_bottlenecks_reports_overdue_and_blocked_counts(client, celery_eager, register_company):
    tokens, _ = register_company()
    token = tokens["access_token"]
    _upload_task_history(client, token)

    response = client.get("/api/v1/tasks/bottlenecks", headers=auth_header(token))
    assert response.status_code == 200
    body = response.json()

    engineering = next(d for d in body if d["department"] == "Engineering")
    assert engineering["overdue_count"] == 1
    assert engineering["blocked_count"] == 1
    assert engineering["task_count"] == 9


def test_repetitive_work_detects_repeated_task_name(client, celery_eager, register_company):
    tokens, _ = register_company()
    token = tokens["access_token"]
    _upload_task_history(client, token)

    response = client.get("/api/v1/tasks/repetitive", headers=auth_header(token))
    assert response.status_code == 200
    body = response.json()

    data_entry_group = next(g for g in body if g["task_name"] == "Data entry")
    assert data_entry_group["display_name"] == "Ada"
    assert data_entry_group["occurrence_count"] == 4
    assert data_entry_group["automation_candidate"] is False  # below the 5-occurrence threshold


def test_redistribution_recommends_moving_work_from_ada_to_max(client, celery_eager, register_company):
    tokens, _ = register_company()
    token = tokens["access_token"]
    _upload_task_history(client, token)

    response = client.get("/api/v1/tasks/redistribution", headers=auth_header(token))
    assert response.status_code == 200
    body = response.json()

    assert len(body) > 0
    assert all(r["from_employee_name"] == "Ada" for r in body)
    assert all(r["to_employee_name"] == "Max" for r in body)


def test_delay_predictions_flags_overdue_task_as_high_risk(client, celery_eager, register_company):
    tokens, _ = register_company()
    token = tokens["access_token"]
    _upload_task_history(client, token)

    response = client.get("/api/v1/tasks/delay-predictions", headers=auth_header(token))
    assert response.status_code == 200
    body = response.json()

    overdue_prediction = next(p for p in body if p["task_name"] == "Legacy migration")
    assert overdue_prediction["probability"] >= 0.5
    assert overdue_prediction["method"] in ("heuristic", "empirical")

    # A task due comfortably in the future should score no higher than the overdue one.
    future_prediction = next(p for p in body if p["task_name"] == "Sprint planning")
    assert future_prediction["probability"] <= overdue_prediction["probability"]


def test_tasks_endpoints_require_authentication(client):
    for path in (
        "/api/v1/tasks",
        "/api/v1/tasks/analysis",
        "/api/v1/tasks/bottlenecks",
        "/api/v1/tasks/repetitive",
        "/api/v1/tasks/redistribution",
        "/api/v1/tasks/delay-predictions",
    ):
        assert client.get(path).status_code == 401
