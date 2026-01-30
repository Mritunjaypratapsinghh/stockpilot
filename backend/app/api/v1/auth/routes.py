from fastapi import APIRouter, HTTPException, Depends
from beanie import PydanticObjectId

from ....models.documents import User
from ....core.security import get_current_user, create_access_token, get_password_hash, verify_password
from ....middleware.rate_limit import rate_limit
from .schemas import UserCreate, UserLogin, Token, UserResponse

router = APIRouter()


@router.post("/register", response_model=Token, dependencies=[Depends(rate_limit("auth"))])
async def register(user_data: UserCreate):
    existing = await User.find_one(User.email == user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_data.email, password_hash=get_password_hash(user_data.password))
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


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user.id), "email": user.email, "settings": user.settings or {}, "telegram_chat_id": user.telegram_chat_id or ""}


@router.put("/settings")
async def update_settings(settings_data: dict, current_user: dict = Depends(get_current_user)):
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "telegram_chat_id" in settings_data:
        user.telegram_chat_id = settings_data["telegram_chat_id"]
    if "email" in settings_data:
        user.email = settings_data["email"]
    
    if not user.settings:
        user.settings = {}
    for k in ["daily_digest", "alerts_enabled", "email_alerts", "hourly_alerts"]:
        if k in settings_data:
            user.settings[k] = settings_data[k]

    await user.save()
    return {"message": "Settings updated"}
