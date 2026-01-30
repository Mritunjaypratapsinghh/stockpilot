from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from beanie import PydanticObjectId

from ....models.documents import User
from ....config import get_settings
from ....core.response_handler import StandardResponse
from ....core.security import get_password_hash, verify_password
from ....middleware.rate_limit import rate_limit
from .schemas import UserCreate, UserLogin, Token, UserResponse, SettingsUpdate

router = APIRouter()
security = HTTPBearer()
settings = get_settings()


def create_access_token(data: dict, email: str = None) -> str:
    to_encode = data.copy()
    if email:
        to_encode["email"] = email
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"_id": user_id, "email": payload.get("email", "")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register", summary="Register new user", description="Create a new user account with email and password", dependencies=[Depends(rate_limit("auth"))])
async def register(user_data: UserCreate):
    existing = await User.find_one(User.email == user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_data.email, password_hash=get_password_hash(user_data.password))
    await user.insert()
    token = create_access_token({"sub": str(user.id)}, email=user_data.email)
    return StandardResponse.ok(Token(access_token=token), "Registration successful")


@router.post("/login", summary="User login", description="Authenticate user and return JWT token", dependencies=[Depends(rate_limit("auth"))])
async def login(user_data: UserLogin):
    user = await User.find_one(User.email == user_data.email)
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)}, email=user.email)
    return StandardResponse.ok(Token(access_token=token), "Login successful")


@router.get("/me", summary="Get current user", description="Get authenticated user profile")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return StandardResponse.ok(UserResponse(
        id=str(user.id), email=user.email, 
        settings=user.settings, telegram_chat_id=user.telegram_chat_id or ""
    ))


@router.put("/settings", summary="Update user settings", description="Update user preferences and notification settings")
async def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)):
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
