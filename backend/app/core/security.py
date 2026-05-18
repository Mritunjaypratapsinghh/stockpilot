"""
Authentication & Security — JWT, password hashing, user extraction.

Token strategy: httpOnly cookie (primary) with Bearer header fallback.
Password strategy: bcrypt with transparent SHA-256 migration.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

# Optional bearer — won't 403 if missing (we check cookie as fallback)
security = HTTPBearer(auto_error=False)

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = settings.access_token_expire_minutes * 60  # seconds


def get_password_hash(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def _is_legacy_sha256(hashed: str) -> bool:
    return len(hashed) == 64 and not hashed.startswith("$")


def verify_password(password: str, hashed: str) -> bool:
    if _is_legacy_sha256(hashed):
        return hashlib.sha256(password.encode()).hexdigest() == hashed
    try:
        return bcrypt.checkpw(password.encode()[:72], hashed.encode())
    except (ValueError, TypeError):
        return False


def needs_rehash(hashed: str) -> bool:
    return _is_legacy_sha256(hashed)


def create_access_token(data: dict, email: str = None) -> str:
    to_encode = data.copy()
    if email:
        to_encode["email"] = email
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def _decode_token(token: str) -> Optional[dict]:
    """Decode JWT and return user dict, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            return None
        return {"_id": user_id, "email": payload.get("email", "")}
    except JWTError:
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Extract user from httpOnly cookie (primary) or Authorization header (fallback)."""
    token = None

    # 1. Try httpOnly cookie first
    token = request.cookies.get(COOKIE_NAME)

    # 2. Fallback to Authorization header (for mobile apps, Swagger, etc.)
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = _decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def get_user_id(current_user: dict) -> PydanticObjectId:
    return PydanticObjectId(current_user["_id"])


def verify_token(token: str) -> dict | None:
    return _decode_token(token)


async def require_pro(current_user: dict = Depends(get_current_user)) -> dict:
    from ..models.documents import User

    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user or not user.is_pro:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    if user.pro_expires_at and user.pro_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Pro subscription expired")
    return current_user
