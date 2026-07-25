"""Business logic for registration, login, token refresh, and password reset.

Multi-tenant isolation: every user belongs to exactly one company_id, set
once at creation (registration or invite) and never taken from client
input on any authenticated request — it always comes from the resolved
User record, so a request can't act on another tenant's data by passing
a different company_id in the payload.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AlreadyExistsError, InvalidCredentialsError, InvalidTokenError, NotAuthenticatedError
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import CompanyRegister, TokenPair, UserInvite, UserLogin

settings = get_settings()


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.tokens = TokenRepository(db)

    # --- Registration & invites ---

    def register_company(self, payload: CompanyRegister) -> TokenPair:
        """Creates a new tenant (Company) plus its first user as ADMIN."""
        if self.users.get_by_email(payload.email):
            raise AlreadyExistsError("An account with this email already exists.")

        company = self.users.create_company(name=payload.company_name)
        user = self.users.create_user(
            company_id=company.id,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=UserRole.ADMIN,
        )
        self.users.commit()
        return self._issue_token_pair(user)

    def invite_user(self, inviter: User, payload: UserInvite) -> User:
        """Admin/Manager creates a teammate inside their own company only."""
        if self.users.get_by_email(payload.email):
            raise AlreadyExistsError("An account with this email already exists.")

        user = self.users.create_user(
            company_id=inviter.company_id,  # always the inviter's own tenant
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role,
        )
        self.users.commit()
        return user

    # --- Login / logout ---

    def login(self, payload: UserLogin) -> TokenPair:
        user = self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InvalidCredentialsError("This account has been deactivated.")

        return self._issue_token_pair(user)

    def logout(self, raw_refresh_token: str) -> None:
        """Revokes a single refresh token (this device/session only)."""
        token_hash = hash_opaque_token(raw_refresh_token)
        token = self.tokens.get_valid_refresh_token(token_hash)
        if token:
            self.tokens.revoke_refresh_token(token)
            self.tokens.commit()

    # --- Refresh ---

    def refresh(self, raw_refresh_token: str) -> TokenPair:
        """Validates + rotates a refresh token: old one is revoked, a new pair issued."""
        token_hash = hash_opaque_token(raw_refresh_token)
        stored = self.tokens.get_valid_refresh_token(token_hash)
        if not stored:
            raise InvalidTokenError("This refresh token is invalid, expired, or already used.")

        user = self.users.get_by_id(stored.user_id)
        if not user or not user.is_active:
            raise InvalidTokenError()

        self.tokens.revoke_refresh_token(stored)  # rotation: old token can't be replayed
        return self._issue_token_pair(user)

    # --- Password reset ---

    def request_password_reset(self, email: str) -> str | None:
        """Returns the raw reset token so the caller (router) can email it.

        Always looks like it succeeded from the outside (no AccountNotFoundError)
        to avoid leaking which emails have accounts. Returns None if the email
        doesn't exist so the caller sends nothing — the response is identical
        either way.
        """
        user = self.users.get_by_email(email)
        if not user:
            logger.info(f"Password reset requested for unknown email: {email}")
            return None

        raw_token = generate_opaque_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.password_reset_token_expire_minutes
        )
        self.tokens.create_reset_token(
            user_id=user.id, token_hash=hash_opaque_token(raw_token), expires_at=expires_at
        )
        self.tokens.commit()
        return raw_token

    def confirm_password_reset(self, raw_token: str, new_password: str) -> None:
        token_hash = hash_opaque_token(raw_token)
        stored = self.tokens.get_valid_reset_token(token_hash)
        if not stored:
            raise InvalidTokenError("This reset link is invalid, expired, or already used.")

        user = self.users.get_by_id(stored.user_id)
        if not user:
            raise InvalidTokenError()

        user.hashed_password = hash_password(new_password)
        self.tokens.mark_reset_token_used(stored)
        self.tokens.revoke_all_for_user(user.id)  # log out every existing session
        self.db.add(user)
        self.tokens.commit()

    # --- Current user resolution ---

    def get_current_user(self, access_token: str) -> User:
        claims = decode_access_token(access_token)
        if not claims or "sub" not in claims:
            raise NotAuthenticatedError()

        user = self.users.get_by_id(claims["sub"])
        if not user or not user.is_active:
            raise NotAuthenticatedError()
        return user

    # --- Internal helpers ---

    def _issue_token_pair(self, user: User) -> TokenPair:
        access_token = create_access_token(subject=str(user.id))

        raw_refresh = generate_opaque_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        self.tokens.create_refresh_token(
            user_id=user.id, token_hash=hash_opaque_token(raw_refresh), expires_at=expires_at
        )
        self.tokens.commit()

        return TokenPair(access_token=access_token, refresh_token=raw_refresh)
