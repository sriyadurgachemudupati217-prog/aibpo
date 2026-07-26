"""Celery tasks. Currently: upload ingestion/extraction (Phase 2).

Each task opens its own DB session — Celery workers are separate
processes from FastAPI, so they can't share the request-scoped
`get_db` session. The session factory is imported at call time (not
at module load) so tests can monkeypatch `app.db.session.SessionLocal`
to point at an in-memory test DB before the task runs.
"""
import json
from pathlib import Path

from app.core.logging import logger
from app.models.upload import Upload, UploadStatus
from app.repositories.upload_repository import UploadRepository
from app.services.ingestion_service import extract_content
from app.workers.celery_app import celery_app


@celery_app.task(name="aibpo.process_upload", bind=True, max_retries=0)
def process_upload_task(self, upload_id: str) -> None:
    """Extracts content from an uploaded file and writes it as JSON.

    Never raises: any failure is caught and recorded on the Upload row
    as status=FAILED with the error message, so the API can surface it
    via GET /uploads/{id}/status instead of the task silently dying.
    """
    from app.db.session import SessionLocal  # runtime import — see module docstring

    db = SessionLocal()
    try:
        repo = UploadRepository(db)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            logger.error(f"process_upload_task: upload {upload_id} not found")
            return

        repo.update_status(upload, UploadStatus.PROCESSING)

        try:
            raw_path = Path(upload.storage_path)
            extracted = extract_content(upload.file_type, raw_path)

            json_path = raw_path.with_suffix(".json")
            json_path.write_text(json.dumps(extracted, default=str, indent=2))

            repo.update_status(upload, UploadStatus.DONE, extracted_data_path=str(json_path))
            logger.info(f"Upload {upload.id} processed successfully -> {json_path}")
        except Exception as exc:  # noqa: BLE001 - any extractor failure lands here, not just specific ones
            logger.exception(f"Upload {upload.id} processing failed: {exc}")
            repo.update_status(upload, UploadStatus.FAILED, error_message=str(exc)[:2000])
    finally:
        db.close()
