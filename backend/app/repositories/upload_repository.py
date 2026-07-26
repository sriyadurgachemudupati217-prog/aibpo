"""DB access for Upload. Every read/write here is scoped by company_id so
one tenant's uploads are never visible to another — see UploadService for
where that scoping is enforced from the resolved current user.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.upload import Upload, UploadStatus


class UploadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Upload:
        upload = Upload(**kwargs)
        self.db.add(upload)
        self.db.flush()
        return upload

    def get_by_id_for_company(self, upload_id: str | uuid.UUID, company_id: str | uuid.UUID) -> Upload | None:
        return (
            self.db.query(Upload)
            .filter(Upload.id == upload_id, Upload.company_id == company_id)
            .first()
        )

    def list_by_company(self, company_id: str | uuid.UUID) -> list[Upload]:
        return (
            self.db.query(Upload)
            .filter(Upload.company_id == company_id)
            .order_by(Upload.created_at.desc())
            .all()
        )

    def update_status(
        self,
        upload: Upload,
        status: UploadStatus,
        extracted_data_path: str | None = None,
        error_message: str | None = None,
    ) -> Upload:
        upload.status = status
        if extracted_data_path is not None:
            upload.extracted_data_path = extracted_data_path
        upload.error_message = error_message
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        return upload

    def delete(self, upload: Upload) -> None:
        self.db.delete(upload)
        self.db.commit()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance) -> None:
        self.db.refresh(instance)
