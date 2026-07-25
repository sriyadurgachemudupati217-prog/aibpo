"""Auth endpoints: registration, login, refresh, logout, password reset, current user."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.logging import logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    CompanyRegister,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenPair,
    UserLogin,
    UserRead,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=201)
def register(payload: CompanyRegister, db: Session = Depends(get_db)) -> TokenPair:
    """Creates a new company (tenant) and its first admin user, returns access + refresh tokens."""
    return AuthService(db).register_company(payload)


@router.post("/login", response_model=TokenPair)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenPair:
    return AuthService(db).login(payload)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Rotates the refresh token: the one submitted is revoked, a new pair is issued."""
    return AuthService(db).refresh(payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> MessageResponse:
    """Revokes the given refresh token (ends that session only)."""
    AuthService(db).logout(payload.refresh_token)
    return MessageResponse(message="Logged out.")


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> MessageResponse:
    """Always returns the same message, whether or not the email has an account,
    so this endpoint can't be used to enumerate registered users."""
    raw_token = AuthService(db).request_password_reset(payload.email)
    if raw_token:
        # Phase 1 has no transactional email provider wired up yet — log it so the
        # flow is testable end-to-end. Replace with a real mailer before production.
        logger.info(f"[DEV ONLY] Password reset token for {payload.email}: {raw_token}")
    return MessageResponse(message="If that email has an account, a reset link has been sent.")


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).confirm_password_reset(payload.token, payload.new_password)
    return MessageResponse(message="Password has been reset. Please log in again.")


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
