"""Request/response schemas for task + task-analysis endpoints."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.task import TaskStatus


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    upload_id: uuid.UUID | None
    employee_id: uuid.UUID | None
    task_name: str
    department: str | None
    status: TaskStatus
    assigned_at: datetime | None
    due_at: datetime | None
    completed_at: datetime | None
    estimated_hours: float | None
    actual_hours: float | None
    delay_probability: float | None


WorkloadFlag = Literal["overloaded", "underloaded", "balanced"]


class EmployeeWorkload(BaseModel):
    employee_id: uuid.UUID
    display_name: str
    department: str | None
    task_count: int
    total_estimated_hours: float
    total_actual_hours: float
    workload_index: float  # ratio of this employee's estimated hours to their department's mean
    flag: WorkloadFlag


class WorkloadAnalysis(BaseModel):
    employees: list[EmployeeWorkload]
    department_mean_hours: dict[str, float]


class DepartmentBottleneck(BaseModel):
    department: str
    task_count: int
    overdue_count: int
    blocked_count: int
    avg_hours_overage: float  # avg(actual_hours - estimated_hours) where both known
    bottleneck_score: float
    is_bottleneck: bool


class RepetitiveTaskGroup(BaseModel):
    employee_id: uuid.UUID
    display_name: str
    task_name: str
    occurrence_count: int
    total_hours: float
    automation_candidate: bool


class RedistributionRecommendation(BaseModel):
    task_id: uuid.UUID
    task_name: str
    estimated_hours: float | None
    from_employee_id: uuid.UUID
    from_employee_name: str
    to_employee_id: uuid.UUID
    to_employee_name: str
    reason: str


class DelayPredictionRead(BaseModel):
    task_id: uuid.UUID
    task_name: str
    employee_id: uuid.UUID | None
    department: str | None
    due_at: datetime | None
    probability: float
    method: Literal["xgboost", "empirical", "heuristic"]
