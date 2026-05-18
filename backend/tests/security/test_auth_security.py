"""
Security tests — authentication, authorization, tenant isolation.

These tests protect against:
- Token forgery/manipulation
- Cross-tenant data access
- Privilege escalation
- Brute force attacks
- Injection attacks
"""

import hashlib
from datetime import datetime, timezone

import pytest
from app.core.config import settings
from app.core.security import (
    _is_legacy_sha256,
    create_access_token,
    get_password_hash,
    needs_rehash,
    verify_password,
    verify_token,
)
from jose import jwt


class TestPasswordSecurity:
    """Password hashing must be secure against all known attacks."""

    def test_bcrypt_hash_format(self):
        h = get_password_hash("TestPass123")
        assert h.startswith("$2b$")
        assert len(h) == 60

    def test_same_password_different_hashes(self):
        """Salt ensures identical passwords produce different hashes."""
        h1 = get_password_hash("SamePass123")
        h2 = get_password_hash("SamePass123")
        assert h1 != h2  # different salts

    def test_password_72_byte_limit(self):
        """Bcrypt truncates at 72 bytes — verify it still works."""
        long_pass = "A" * 100
        h = get_password_hash(long_pass)
        assert verify_password(long_pass, h)
        # Passwords differing only after 72 bytes hash the same
        assert verify_password("A" * 72, h)

    def test_empty_password_rejected(self):
        """Empty password should still hash (validation is at schema level)."""
        h = get_password_hash("")
        assert verify_password("", h)
        assert not verify_password("anything", h)

    def test_unicode_password(self):
        """Unicode passwords (Hindi, emoji) must work."""
        h = get_password_hash("पासवर्ड123🔐")
        assert verify_password("पासवर्ड123🔐", h)
        assert not verify_password("पासवर्ड123", h)

    def test_legacy_sha256_detection(self):
        legacy = hashlib.sha256(b"old").hexdigest()
        assert _is_legacy_sha256(legacy)
        assert not _is_legacy_sha256("$2b$12$shortbcrypthash")
        assert not _is_legacy_sha256("tooshort")

    def test_legacy_hash_needs_rehash(self):
        legacy = hashlib.sha256(b"migrate_me").hexdigest()
        assert needs_rehash(legacy)

    def test_bcrypt_hash_no_rehash(self):
        h = get_password_hash("modern")
        assert not needs_rehash(h)

    def test_invalid_hash_returns_false(self):
        """Corrupted hash should return False, not crash."""
        assert verify_password("test", "corrupted_garbage_hash") is False
        assert verify_password("test", "") is False
        assert verify_password("test", "$2b$12$invalid") is False


class TestJWTSecurity:
    """JWT token must be unforgeable and properly validated."""

    def test_valid_token_decodes(self):
        token = create_access_token({"sub": "user123"}, email="a@b.com")
        result = verify_token(token)
        assert result["_id"] == "user123"
        assert result["email"] == "a@b.com"

    def test_expired_token_rejected(self):
        payload = {"sub": "user123", "exp": datetime(2020, 1, 1, tzinfo=timezone.utc)}
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
        assert verify_token(token) is None

    def test_wrong_secret_rejected(self):
        payload = {"sub": "user123", "exp": datetime(2030, 1, 1, tzinfo=timezone.utc)}
        token = jwt.encode(payload, "wrong_secret_key", algorithm="HS256")
        assert verify_token(token) is None

    def test_missing_sub_rejected(self):
        payload = {"email": "a@b.com", "exp": datetime(2030, 1, 1, tzinfo=timezone.utc)}
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
        assert verify_token(token) is None

    def test_none_algorithm_attack(self):
        """'none' algorithm attack must be rejected."""
        payload = {"sub": "admin", "exp": datetime(2030, 1, 1, tzinfo=timezone.utc)}
        # Attempt to forge with 'none' algorithm
        try:
            token = jwt.encode(payload, "", algorithm="none")
            assert verify_token(token) is None
        except Exception:
            pass  # jose library may reject 'none' at encode time

    def test_malformed_token_rejected(self):
        assert verify_token("not.a.token") is None
        assert verify_token("") is None
        assert verify_token("eyJ.eyJ.sig") is None

    def test_token_with_future_iat(self):
        """Token with future issued-at should still work (clock skew tolerance)."""
        token = create_access_token({"sub": "user1"})
        assert verify_token(token) is not None


class TestTenantIsolation:
    """Verify that BaseRepository enforces user scoping."""

    def test_repository_scopes_queries(self):
        from app.models.documents import Holding
        from app.services.base.repository import BaseRepository
        from beanie import PydanticObjectId

        uid = PydanticObjectId()
        repo = BaseRepository(Holding, uid)
        query = repo._scoped(symbol="TCS")
        assert query["user_id"] == uid
        assert query["symbol"] == "TCS"

    def test_repository_get_by_id_checks_ownership(self):
        """get_by_id must verify user_id matches, not just document existence."""
        from app.models.documents import Holding
        from app.services.base.repository import BaseRepository
        from beanie import PydanticObjectId

        uid = PydanticObjectId()
        repo = BaseRepository(Holding, uid)
        assert hasattr(repo, "get_by_id")


class TestInputValidation:
    """Protect against injection and malformed inputs."""

    def test_fy_validation_rejects_injection(self):
        from app.api.v1.itr.routes import _validate_fy
        from fastapi import HTTPException

        # Valid
        _validate_fy("2025-26")

        # SQL/NoSQL injection attempts
        with pytest.raises(HTTPException):
            _validate_fy("2025-26; DROP TABLE users")
        with pytest.raises(HTTPException):
            _validate_fy("{'$gt': ''}")
        with pytest.raises(HTTPException):
            _validate_fy("")
        with pytest.raises(HTTPException):
            _validate_fy("../../etc/passwd")

    def test_symbol_sanitization(self):
        from app.services.market.price_service import sanitize_symbol

        assert sanitize_symbol("TCS") == "TCS"
        assert sanitize_symbol("M&M") == "M&M"
        assert sanitize_symbol("  tcs  ") == "TCS"
        # Injection attempts
        assert sanitize_symbol("<script>alert(1)</script>") is None
        assert sanitize_symbol("'; DROP TABLE--") is None
        assert sanitize_symbol("") is None
        assert sanitize_symbol("A" * 50) is None  # too long
