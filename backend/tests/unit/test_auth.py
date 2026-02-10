"""Unit tests for authentication"""

from app.core.security import create_access_token, get_password_hash, verify_password


def test_password_hash():
    password = "testpassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 20


def test_verify_password():
    password = "testpassword123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    token = create_access_token({"sub": "user123"}, email="test@example.com")
    assert token is not None
    assert len(token) > 50
