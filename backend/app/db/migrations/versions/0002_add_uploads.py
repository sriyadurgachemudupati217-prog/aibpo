"""add uploads table

Revision ID: 0002_add_uploads
Revises: 0001_initial
Create Date: 2026-07-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_add_uploads"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

file_type_enum = postgresql.ENUM(
    "csv", "xlsx", "pdf", "docx", "png", "jpg", name="upload_file_type"
)
upload_status_enum = postgresql.ENUM(
    "pending", "processing", "done", "failed", name="upload_status"
)


def upgrade() -> None:
    bind = op.get_bind()
    file_type_enum.create(bind, checkfirst=True)
    upload_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", file_type_enum, nullable=False),
        sa.Column("status", upload_status_enum, nullable=False, server_default="pending"),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("extracted_data_path", sa.String(length=1024), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_uploads_company_id", "uploads", ["company_id"])
    op.create_index("ix_uploads_uploaded_by", "uploads", ["uploaded_by"])


def downgrade() -> None:
    op.drop_index("ix_uploads_uploaded_by", table_name="uploads")
    op.drop_index("ix_uploads_company_id", table_name="uploads")
    op.drop_table("uploads")
    upload_status_enum.drop(op.get_bind(), checkfirst=True)
    file_type_enum.drop(op.get_bind(), checkfirst=True)
