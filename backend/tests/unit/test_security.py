"""Unit tests for password hashing and JWT round-trip."""
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    plain = "correct-horse-battery-staple"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_roundtrip() -> None:
    token = create_access_token(subject="user-123")
    claims = decode_access_token(token)
    assert claims is not None
    assert claims["sub"] == "user-123"


def test_jwt_rejects_garbage_token() -> None:
    assert decode_access_token("not-a-real-token") is None
