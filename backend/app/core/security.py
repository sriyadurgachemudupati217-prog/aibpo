"""Password hashing, JWT issuance/verification, and opaque secure tokens.

Two token families:
- Access/refresh JWTs (short-lived access, longer-lived refresh) carry a
  "type" claim so one can never be used in place of the other.
- Opaque tokens (refresh token's raw value, password-reset token) are
  random strings; only their SHA-256 hash is ever stored in the DB, so a
  DB read alone can't be replayed as a valid token.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_jwt(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: dict[str, Any] = {"sub": subject, "type": token_type, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str) -> str:
    return _create_jwt(
        subject, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any] | None:
    """Decodes a JWT and verifies both signature/expiry and the `type` claim."""
    try:
        claims = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
    if claims.get("type") != expected_type:
        return None
    return claims


def decode_access_token(token: str) -> dict[str, Any] | None:
    return decode_token(token, "access")


def generate_opaque_token() -> str:
    """A random, URL-safe token for refresh sessions and password resets."""
    return secrets.token_urlsafe(48)


def hash_opaque_token(raw_token: str) -> str:
    """SHA-256 is fine here (not a password): the input already has ~256 bits
    of entropy from `secrets.token_urlsafe`, so it's not brute-forceable."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
