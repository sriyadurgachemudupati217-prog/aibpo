"""Business logic for uploads: validation, on-disk storage, DB bookkeeping,
and handing off to Celery for extraction.

Multi-tenant isolation: every read/update/delete here takes the
resolved current_user and scopes the query by current_user.company_id —
never by a company_id supplied in the request path or body.
"""
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    PermissionDeniedError,
    UnsupportedFileTypeError,
)
from app.core.logging import logger
from app.models.upload import FileType, Upload, UploadCategory, UploadStatus
from app.models.user import User, UserRole
from app.repositories.upload_repository import UploadRepository

settings = get_settings()

_EXTENSION_TO_FILE_TYPE = {
    "csv": FileType.CSV,
    "xlsx": FileType.XLSX,
    "pdf": FileType.PDF,
    "docx": FileType.DOCX,
    "png": FileType.PNG,
    "jpg": FileType.JPG,
    "jpeg": FileType.JPG,
}


class UploadService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UploadRepository(db)

    # --- Create ---

    def create_upload(
        self,
        current_user: User,
        filename: str,
        content: bytes,
        category: UploadCategory = UploadCategory.OTHER,
    ) -> Upload:
        file_type = self._resolve_file_type(filename)
        self._enforce_size_limit(len(content))

        upload_id = uuid.uuid4()
        company_dir = Path(settings.upload_storage_path) / str(current_user.company_id)
        company_dir.mkdir(parents=True, exist_ok=True)

        extension = filename.rsplit(".", 1)[-1].lower()
        storage_path = company_dir / f"{upload_id}.{extension}"
        storage_path.write_bytes(content)

        upload = self.repo.create(
            id=upload_id,
            company_id=current_user.company_id,
            uploaded_by=current_user.id,
            original_filename=filename,
            file_type=file_type,
            category=category,
            status=UploadStatus.PENDING,
            storage_path=str(storage_path),
            file_size_bytes=len(content),
        )
        self.repo.commit()
        self.repo.refresh(upload)

        self._enqueue_processing(upload.id)
        return upload

    # --- Read ---

    def get_upload(self, current_user: User, upload_id: str | uuid.UUID) -> Upload:
        upload = self.repo.get_by_id_for_company(upload_id, current_user.company_id)
        if not upload:
            raise NotFoundError("Upload not found.")
        return upload

    def list_uploads(self, current_user: User) -> list[Upload]:
        return self.repo.list_by_company(current_user.company_id)

    # --- Delete ---

    def delete_upload(self, current_user: User, upload_id: str | uuid.UUID) -> None:
        upload = self.get_upload(current_user, upload_id)

        is_owner = upload.uploaded_by == current_user.id
        is_privileged = current_user.role in (UserRole.ADMIN, UserRole.MANAGER)
        if not (is_owner or is_privileged):
            raise PermissionDeniedError("You can only delete your own uploads.")

        self._delete_files(upload)
        self.repo.delete(upload)

    # --- Internal helpers ---

    def _resolve_file_type(self, filename: str) -> FileType:
        if "." not in filename:
            raise UnsupportedFileTypeError("File has no extension.")
        extension = filename.rsplit(".", 1)[-1].lower()
        file_type = _EXTENSION_TO_FILE_TYPE.get(extension)
        if not file_type:
            raise UnsupportedFileTypeError(
                f"'.{extension}' is not supported. Allowed types: "
                f"{', '.join(sorted(set(t.value for t in FileType)))}."
            )
        return file_type

    def _enforce_size_limit(self, size_bytes: int) -> None:
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise FileTooLargeError(
                f"File exceeds the {settings.max_upload_size_mb}MB upload limit."
            )

    def _enqueue_processing(self, upload_id: uuid.UUID) -> None:
        from app.workers.tasks import process_upload_task

        process_upload_task.delay(str(upload_id))
        logger.info(f"Queued processing for upload {upload_id}")

    def _delete_files(self, upload: Upload) -> None:
        for path_str in (upload.storage_path, upload.extracted_data_path):
            if not path_str:
                continue
            path = Path(path_str)
            if path.exists():
                path.unlink()
