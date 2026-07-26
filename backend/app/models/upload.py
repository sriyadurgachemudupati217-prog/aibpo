"""Upload model: one row per file a user uploads for ingestion.

Isolation: every query against this table must filter by company_id,
scoped from the resolved current user — see UploadRepository. The raw
file lives on disk at `storage_path`; once Celery finishes extraction,
`extracted_data_path` points at the resulting JSON.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class FileType(str, enum.Enum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"
    JPG = "jpg"


class UploadStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Upload(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uploads"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType, name="upload_file_type"), nullable=False)
    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus, name="upload_status"), default=UploadStatus.PENDING, nullable=False
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    extracted_data_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
