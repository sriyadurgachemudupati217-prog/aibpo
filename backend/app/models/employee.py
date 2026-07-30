"""Employee model: a lightweight roster entry resolved from uploaded data
(task history, attendance, etc.), not the same as a `User` login account.

`external_id` is whatever identifies the employee in the source file —
usually their name, sometimes an employee code — normalized (trimmed,
lowercased) so "Ada Lovelace" and "ada lovelace" resolve to one row.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class Employee(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("company_id", "external_id", name="uq_employee_company_external_id"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
