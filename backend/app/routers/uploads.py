"""Upload endpoints. All routes require authentication and are scoped to
the caller's own company — see UploadService for the isolation logic."""
from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadCategory
from app.models.user import User
from app.schemas.upload import UploadRead, UploadStatusRead
from app.services.upload_service import UploadService

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadRead, status_code=201)
async def create_upload(
    file: UploadFile,
    category: UploadCategory = Form(UploadCategory.OTHER),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadRead:
    """Saves the file to disk under storage/uploads/{company_id}/ and queues
    async extraction via Celery. `category` tells downstream pipelines what
    kind of data this is (e.g. task_history triggers Task/Employee ingestion
    once extraction succeeds — see app.workers.tasks). Returns immediately
    with status=pending."""
    content = await file.read()
    upload = UploadService(db).create_upload(
        current_user=current_user,
        filename=file.filename or "unnamed",
        content=content,
        category=category,
    )
    return upload


@router.get("", response_model=list[UploadRead])
def list_uploads(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[UploadRead]:
    return UploadService(db).list_uploads(current_user)


@router.get("/{upload_id}", response_model=UploadRead)
def get_upload(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadRead:
    return UploadService(db).get_upload(current_user, upload_id)


@router.get("/{upload_id}/status", response_model=UploadStatusRead)
def get_upload_status(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadStatusRead:
    """Lightweight endpoint for the frontend to poll while a file is processing."""
    return UploadService(db).get_upload(current_user, upload_id)


@router.delete("/{upload_id}", status_code=204)
def delete_upload(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Owner, Admin, or Manager may delete an upload; other Employees may not."""
    UploadService(db).delete_upload(current_user, upload_id)
