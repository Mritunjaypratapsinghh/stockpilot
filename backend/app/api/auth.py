from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import hashlib
from ..database import get_db
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
        # Return cached user data from JWT - no DB query needed
        return {"_id": user_id, "email": payload.get("email", "")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register", response_model=Token, dependencies=[Depends(rate_limit("auth"))])
async def register(user_data: UserCreate):
    db = get_db()
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "settings": {"alerts_enabled": True, "daily_digest": True},
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.users.insert_one(user_doc)
    token = create_access_token({"sub": str(result.inserted_id)}, email=user_data.email)
    return {"access_token": token}

@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit("auth"))])
async def login(user_data: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user["_id"])}, email=user["email"])
    return {"access_token": token}

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # Fetch full user data from DB for /me endpoint
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user["_id"]), "email": user["email"], "settings": user.get("settings", {}), "telegram_chat_id": user.get("telegram_chat_id", "")}


@router.put("/settings")
async def update_settings(settings_data: dict, current_user: dict = Depends(get_current_user)):
    db = get_db()
    update_doc = {}
    if "telegram_chat_id" in settings_data:
        update_doc["telegram_chat_id"] = settings_data["telegram_chat_id"]
    if "email" in settings_data:
        update_doc["email"] = settings_data["email"]
    allowed = {"daily_digest", "alerts_enabled", "email_alerts", "hourly_alerts"}
    for k in allowed:
        if k in settings_data:
            update_doc[f"settings.{k}"] = settings_data[k]
    if update_doc:
        await db.users.update_one({"_id": ObjectId(current_user["_id"])}, {"$set": update_doc})
    return {"message": "Settings updated"}
