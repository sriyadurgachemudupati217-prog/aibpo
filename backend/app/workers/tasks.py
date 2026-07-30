"""Celery tasks: upload extraction (Phase 2) plus task-history ingestion
into structured Task/Employee rows (Phase 3).

Each task opens its own DB session — Celery workers are separate
processes from FastAPI, so they can't share the request-scoped
`get_db` session. The session factory is imported at call time (not
at module load) so tests can monkeypatch `app.db.session.SessionLocal`
to point at an in-memory test DB before the task runs.
"""
import json
from pathlib import Path

from app.core.logging import logger
from app.models.upload import FileType, Upload, UploadCategory, UploadStatus
from app.repositories.upload_repository import UploadRepository
from app.services.ingestion_service import extract_content
from app.services.task_ingestion_service import ingest_task_history
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

            # Phase 3: task-history files also get parsed into structured
            # Task/Employee rows. Kept as a best-effort secondary step — a
            # failure here doesn't undo the successful raw extraction above,
            # it's just surfaced via error_message alongside status=DONE.
            if upload.category == UploadCategory.TASK_HISTORY and upload.file_type in (
                FileType.CSV,
                FileType.XLSX,
            ):
                try:
                    count = ingest_task_history(db, upload.company_id, upload.id, raw_path)
                    logger.info(f"Upload {upload.id}: ingested {count} tasks")
                except Exception as exc:  # noqa: BLE001
                    logger.exception(f"Upload {upload.id}: task ingestion failed: {exc}")
                    repo.update_status(
                        upload,
                        UploadStatus.DONE,
                        error_message=f"File processed, but task ingestion failed: {str(exc)[:1900]}",
                    )
        except Exception as exc:  # noqa: BLE001 - any extractor failure lands here, not just specific ones
            logger.exception(f"Upload {upload.id} processing failed: {exc}")
            repo.update_status(upload, UploadStatus.FAILED, error_message=str(exc)[:2000])
    finally:
        db.close()
