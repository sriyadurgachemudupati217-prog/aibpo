"""phase 3: task analysis (upload category, employees, tasks)

Revision ID: 0003_task_analysis
Revises: 0002_add_uploads
Create Date: 2026-07-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_task_analysis"
down_revision: Union[str, None] = "0002_add_uploads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

upload_category_enum = postgresql.ENUM(
    "task_history", "tickets", "sales", "meetings", "attendance", "projects", "other",
    name="upload_category",
)
task_status_enum = postgresql.ENUM(
    "not_started", "in_progress", "completed", "blocked", name="task_status"
)


def upgrade() -> None:
    bind = op.get_bind()
    upload_category_enum.create(bind, checkfirst=True)
    task_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "uploads",
        sa.Column(
            "category", upload_category_enum, nullable=False, server_default="other"
        ),
    )

    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "external_id", name="uq_employee_company_external_id"),
    )
    op.create_index("ix_employees_company_id", "employees", ["company_id"])

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "upload_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("uploads.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("task_name", sa.String(length=500), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("status", task_status_enum, nullable=False, server_default="not_started"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_hours", sa.Float(), nullable=True),
        sa.Column("actual_hours", sa.Float(), nullable=True),
        sa.Column("delay_probability", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tasks_company_id", "tasks", ["company_id"])
    op.create_index("ix_tasks_upload_id", "tasks", ["upload_id"])
    op.create_index("ix_tasks_employee_id", "tasks", ["employee_id"])
    op.create_index("ix_tasks_department", "tasks", ["department"])


def downgrade() -> None:
    op.drop_index("ix_tasks_department", table_name="tasks")
    op.drop_index("ix_tasks_employee_id", table_name="tasks")
    op.drop_index("ix_tasks_upload_id", table_name="tasks")
    op.drop_index("ix_tasks_company_id", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("ix_employees_company_id", table_name="employees")
    op.drop_table("employees")

    op.drop_column("uploads", "category")

    task_status_enum.drop(op.get_bind(), checkfirst=True)
    upload_category_enum.drop(op.get_bind(), checkfirst=True)
