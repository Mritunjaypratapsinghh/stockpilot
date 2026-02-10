"""Authentication routes for user registration, login, and settings."""

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests
from google.oauth2 import id_token

from ....core.config import settings
from ....core.response_handler import StandardResponse
from ....core.security import create_access_token, get_current_user, get_password_hash, verify_password
from ....middleware.rate_limit import rate_limit
from ....models.documents import User
from .schemas import GoogleAuth, SettingsUpdate, Token, UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post(
    "/register",
    summary="Register new user",
    description="Create a new user account with email and password",
    dependencies=[Depends(rate_limit("auth"))],
)
async def register(user_data: UserCreate) -> StandardResponse:
    """Register a new user account."""
    existing = await User.find_one(User.email == user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_data.email, password_hash=get_password_hash(user_data.password))
    await user.insert()
    token = create_access_token({"sub": str(user.id)}, email=user_data.email)
    return StandardResponse.ok(Token(access_token=token), "Registration successful")


@router.post(
    "/login",
    summary="User login",
    description="Authenticate user and return JWT token",
    dependencies=[Depends(rate_limit("auth"))],
)
async def login(user_data: UserLogin) -> StandardResponse:
    """Authenticate user and return JWT token."""
    user = await User.find_one(User.email == user_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.password_hash or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)}, email=user.email)
    return StandardResponse.ok(Token(access_token=token), "Login successful")


@router.post(
    "/google",
    summary="Google OAuth",
    description="Authenticate with Google",
    dependencies=[Depends(rate_limit("auth"))],
)
async def google_auth(data: GoogleAuth) -> StandardResponse:
    """Authenticate or register user via Google OAuth."""
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
    return StandardResponse.ok(Token(access_token=token), "Login successful")


@router.get("/me", summary="Get current user", description="Get authenticated user profile")
async def get_me(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get current authenticated user profile."""
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return StandardResponse.ok(
        UserResponse(
            id=str(user.id), email=user.email, settings=user.settings, telegram_chat_id=user.telegram_chat_id or ""
        )
    )


@router.put(
    "/settings", summary="Update user settings", description="Update user preferences and notification settings"
)
async def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Update user settings and preferences."""
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.telegram_chat_id is not None:
        user.telegram_chat_id = data.telegram_chat_id
    if data.email is not None:
        user.email = data.email

    for field in ["daily_digest", "alerts_enabled", "email_alerts", "hourly_alerts"]:
        val = getattr(data, field)
        if val is not None:
            user.settings[field] = val

    await user.save()
    return StandardResponse.ok(message="Settings updated")
