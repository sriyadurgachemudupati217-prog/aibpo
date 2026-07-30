"""Request/response schemas for upload endpoints."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.upload import FileType, UploadCategory, UploadStatus


class UploadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    uploaded_by: uuid.UUID
    original_filename: str
    file_type: FileType
    category: UploadCategory
    status: UploadStatus
    file_size_bytes: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class UploadStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: UploadStatus
    error_message: str | None
    updated_at: datetime
