"""User management within the caller's own company.

Every query here is scoped by `current_user.company_id` — never by a
company_id the client supplies — so one tenant can never list or modify
another tenant's users.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserInvite, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[User]:
    """Any authenticated user can see their own company's team roster."""
    return UserRepository(db).list_by_company(current_user.company_id)


@router.post("", response_model=UserRead, status_code=201)
def invite_user(
    payload: UserInvite,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: Session = Depends(get_db),
) -> User:
    """Admin or Manager adds a teammate to their own company."""
    return AuthService(db).invite_user(inviter=current_user, payload=payload)
