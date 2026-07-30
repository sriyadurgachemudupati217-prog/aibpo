"""Ingests a task-history file (CSV/XLSX) into Employee + Task rows.

Triggered from app.workers.tasks once a file tagged
UploadCategory.TASK_HISTORY finishes extraction successfully. Column
names are matched flexibly (case-insensitive, common synonyms) since
real-world exports rarely agree on exact headers.
"""
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.task import TaskStatus
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.task_repository import TaskRepository

_COLUMN_ALIASES: dict[str, list[str]] = {
    "employee": ["employee", "employee_name", "assignee", "name", "employee name"],
    "department": ["department", "dept", "team"],
    "task_name": ["task_name", "task", "title", "description", "task name"],
    "status": ["status"],
    "assigned_at": ["assigned_at", "assigned_date", "start_date", "assigned"],
    "due_at": ["due_at", "due_date", "deadline"],
    "completed_at": ["completed_at", "completed_date", "finish_date", "completion_date"],
    "estimated_hours": ["estimated_hours", "est_hours", "estimate", "estimated hours"],
    "actual_hours": ["actual_hours", "hours_spent", "actual", "actual hours"],
}

_STATUS_ALIASES: dict[str, TaskStatus] = {
    "done": TaskStatus.COMPLETED,
    "complete": TaskStatus.COMPLETED,
    "completed": TaskStatus.COMPLETED,
    "in progress": TaskStatus.IN_PROGRESS,
    "in_progress": TaskStatus.IN_PROGRESS,
    "ongoing": TaskStatus.IN_PROGRESS,
    "blocked": TaskStatus.BLOCKED,
    "stuck": TaskStatus.BLOCKED,
    "not started": TaskStatus.NOT_STARTED,
    "not_started": TaskStatus.NOT_STARTED,
    "todo": TaskStatus.NOT_STARTED,
    "pending": TaskStatus.NOT_STARTED,
}


def _resolve_columns(columns: list[str]) -> dict[str, str]:
    """Maps our canonical field names to whatever column actually exists."""
    lower_lookup = {c.strip().lower(): c for c in columns}
    resolved: dict[str, str] = {}
    for field, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_lookup:
                resolved[field] = lower_lookup[alias]
                break
    return resolved


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def _parse_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_status(value: Any) -> TaskStatus:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return TaskStatus.NOT_STARTED
    return _STATUS_ALIASES.get(str(value).strip().lower(), TaskStatus.NOT_STARTED)


def load_dataframe(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)
    return pd.read_csv(path)


def ingest_task_history(
    db: Session, company_id, upload_id, file_path: Path
) -> int:
    """Parses `file_path` and creates Employee/Task rows for `company_id`.

    Idempotent per upload: clears any tasks previously ingested from this
    same upload_id before inserting, so retries don't duplicate rows.
    Returns the number of tasks created.
    """
    df = load_dataframe(file_path)
    columns = _resolve_columns(list(df.columns))

    if "employee" not in columns or "task_name" not in columns:
        raise ValueError(
            "Task history file must have an employee/assignee column and a "
            "task name/title column."
        )

    employees = EmployeeRepository(db)
    tasks = TaskRepository(db)
    tasks.delete_by_upload(upload_id)

    created = 0
    for _, row in df.iterrows():
        raw_employee = row.get(columns["employee"])
        if raw_employee is None or (isinstance(raw_employee, float) and pd.isna(raw_employee)):
            continue  # a task with no assignee can't be attributed — skip it
        display_name = str(raw_employee).strip()
        external_id = display_name.lower()

        raw_department = row.get(columns["department"]) if "department" in columns else None
        department = (
            str(raw_department).strip()
            if raw_department is not None and not (isinstance(raw_department, float) and pd.isna(raw_department))
            else None
        )

        employee = employees.get_or_create(
            company_id=company_id,
            external_id=external_id,
            display_name=display_name,
            department=department,
        )

        raw_task_name = row.get(columns["task_name"])
        task_name = str(raw_task_name).strip() if raw_task_name is not None else "Untitled task"

        tasks.create(
            company_id=company_id,
            upload_id=upload_id,
            employee_id=employee.id,
            task_name=task_name,
            department=department,
            status=_parse_status(row.get(columns.get("status"))) if "status" in columns else TaskStatus.NOT_STARTED,
            assigned_at=_parse_datetime(row.get(columns.get("assigned_at"))) if "assigned_at" in columns else None,
            due_at=_parse_datetime(row.get(columns.get("due_at"))) if "due_at" in columns else None,
            completed_at=_parse_datetime(row.get(columns.get("completed_at"))) if "completed_at" in columns else None,
            estimated_hours=_parse_float(row.get(columns.get("estimated_hours"))) if "estimated_hours" in columns else None,
            actual_hours=_parse_float(row.get(columns.get("actual_hours"))) if "actual_hours" in columns else None,
        )
        created += 1

    employees.commit()
    tasks.commit()
    logger.info(f"Ingested {created} tasks from upload {upload_id} (company {company_id})")
    return created
