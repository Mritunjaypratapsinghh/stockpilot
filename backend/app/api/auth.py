from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from beanie import PydanticObjectId
import hashlib

from ..models.documents import User
from ..config import get_settings
from ..models import UserCreate, UserLogin, Token
from ..middleware.rate_limit import rate_limit

router = APIRouter()
security = HTTPBearer()
settings = get_settings()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


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


@router.post("/register", response_model=Token, dependencies=[Depends(rate_limit("auth"))])
async def register(user_data: UserCreate):
    existing = await User.find_one(User.email == user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_data.email, password_hash=hash_password(user_data.password))
    await user.insert()
    token = create_access_token({"sub": str(user.id)}, email=user_data.email)
    return {"access_token": token}


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit("auth"))])
async def login(user_data: UserLogin):
    user = await User.find_one(User.email == user_data.email)
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)}, email=user.email)
    return {"access_token": token}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user.id), "email": user.email, "settings": user.settings, "telegram_chat_id": user.telegram_chat_id or ""}


@router.put("/settings")
async def update_settings(settings_data: dict, current_user: dict = Depends(get_current_user)):
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "telegram_chat_id" in settings_data:
        user.telegram_chat_id = settings_data["telegram_chat_id"]
    if "email" in settings_data:
        user.email = settings_data["email"]
    
    allowed = {"daily_digest", "alerts_enabled", "email_alerts", "hourly_alerts"}
    for k in allowed:
        if k in settings_data:
            user.settings[k] = settings_data[k]

    await user.save()
    return {"message": "Settings updated"}
