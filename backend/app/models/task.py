"""Task model: one row per task, ingested from a task-history CSV upload
(see app.services.task_ingestion_service). Feeds workload/bottleneck
analysis and the delay-prediction model in app.ml.delay_prediction.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class TaskStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    upload_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )

    task_name: Mapped[str] = mapped_column(String(500), nullable=False)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.NOT_STARTED, nullable=False
    )

    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Populated on demand by app.ml.delay_prediction — null until scored.
    delay_probability: Mapped[float | None] = mapped_column(Float, nullable=True)

    @property
    def is_overdue(self) -> bool:
        if self.status == TaskStatus.COMPLETED or self.due_at is None:
            return False
        from datetime import timezone

        return datetime.now(timezone.utc) > self.due_at

    @property
    def was_delayed(self) -> bool | None:
        """None if we can't determine this yet (not completed, or missing dates)."""
        if self.status != TaskStatus.COMPLETED or not self.due_at or not self.completed_at:
            return None
        return self.completed_at > self.due_at
