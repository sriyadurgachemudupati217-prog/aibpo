"""DB access for refresh tokens and password reset tokens."""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Refresh tokens ---

    def create_refresh_token(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(token)
        self.db.flush()
        return token

    def get_valid_refresh_token(self, token_hash: str) -> RefreshToken | None:
        return (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

    def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.revoked = True
        self.db.add(token)

    def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
            {"revoked": True}
        )

    # --- Password reset tokens ---

    def create_reset_token(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        token = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(token)
        self.db.flush()
        return token

    def get_valid_reset_token(self, token_hash: str) -> PasswordResetToken | None:
        return (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

    def mark_reset_token_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        self.db.add(token)

    def commit(self) -> None:
        self.db.commit()
