"""Shared FastAPI dependencies used across routers."""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    return AuthService(db).get_current_user(token)


def require_roles(*allowed: UserRole):
    """Dependency factory: `Depends(require_roles(UserRole.ADMIN))` guards a route by role."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise PermissionDeniedError()
        return user

    return _check
