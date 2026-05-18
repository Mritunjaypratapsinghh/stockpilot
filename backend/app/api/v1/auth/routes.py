"""Authentication routes — login, register, Google OAuth, logout."""

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Response
from google.auth.transport import requests
from google.oauth2 import id_token

from ....core.config import settings
from ....core.response_handler import StandardResponse
from ....core.security import (
    COOKIE_MAX_AGE,
    COOKIE_NAME,
    create_access_token,
    get_current_user,
    get_password_hash,
    needs_rehash,
    verify_password,
)
from ....middleware.rate_limit import rate_limit
from ....models.documents import User
from .schemas import GoogleAuth, SettingsUpdate, Token, UserCreate, UserLogin, UserResponse

router = APIRouter()


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set httpOnly secure cookie with JWT token."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",  # Required for cross-origin (frontend ≠ backend domain)
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


@router.post(
    "/register",
    summary="Register new user",
    dependencies=[Depends(rate_limit("auth"))],
)
async def register(user_data: UserCreate, response: Response) -> StandardResponse:
    """Register a new user account. Sets httpOnly auth cookie."""
    existing = await User.find_one(User.email == user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_data.email, password_hash=get_password_hash(user_data.password))
    await user.insert()
    token = create_access_token({"sub": str(user.id)}, email=user_data.email)
    _set_auth_cookie(response, token)
    return StandardResponse.ok(Token(access_token=token), "Registration successful")


@router.post(
    "/login",
    summary="User login",
    dependencies=[Depends(rate_limit("auth"))],
)
async def login(user_data: UserLogin, response: Response) -> StandardResponse:
    """Authenticate user. Sets httpOnly auth cookie. Auto-upgrades legacy hashes."""
    user = await User.find_one(User.email == user_data.email)
    if not user or not user.password_hash or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if needs_rehash(user.password_hash):
        user.password_hash = get_password_hash(user_data.password)
        await user.save()

    token = create_access_token({"sub": str(user.id)}, email=user.email)
    _set_auth_cookie(response, token)
    return StandardResponse.ok(Token(access_token=token), "Login successful")


@router.post(
    "/google",
    summary="Google OAuth",
    dependencies=[Depends(rate_limit("auth"))],
)
async def google_auth(data: GoogleAuth, response: Response) -> StandardResponse:
    """Authenticate via Google OAuth. Sets httpOnly auth cookie."""
    try:
        idinfo = id_token.verify_oauth2_token(data.credential, requests.Request(), settings.google_client_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email, google_id = idinfo["email"], idinfo["sub"]
    name = idinfo.get("name")

    user = await User.find_one(User.email == email)
    if user:
        if not user.google_id:
            user.google_id = google_id
            await user.save()
    else:
        user = User(email=email, google_id=google_id, name=name)
        await user.insert()

    token = create_access_token({"sub": str(user.id)}, email=email)
    _set_auth_cookie(response, token)
    return StandardResponse.ok(Token(access_token=token), "Login successful")


@router.post("/logout", summary="Logout")
async def logout(response: Response) -> StandardResponse:
    """Clear auth cookie."""
    response.delete_cookie(key=COOKIE_NAME, path="/", httponly=True, secure=True, samesite="none")
    return StandardResponse.ok(message="Logged out")


@router.get("/me", summary="Get current user")
async def get_me(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return StandardResponse.ok(
        UserResponse(
            id=str(user.id),
            email=user.email,
            settings=user.settings,
            telegram_chat_id=user.telegram_chat_id or "",
            is_pro=user.is_pro,
        )
    )


@router.put("/settings", summary="Update user settings")
async def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.telegram_chat_id is not None:
        user.telegram_chat_id = data.telegram_chat_id
    if data.email is not None:
        user.email = data.email

    for field in ["daily_digest", "alerts_enabled", "email_alerts", "hourly_alerts", "privacy_mode"]:
        val = getattr(data, field)
        if val is not None:
            user.settings[field] = val

    await user.save()
    return StandardResponse.ok(message="Settings updated")
