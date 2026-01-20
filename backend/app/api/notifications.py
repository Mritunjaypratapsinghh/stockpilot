from fastapi import APIRouter, Depends
from datetime import datetime
from bson import ObjectId
from ..database import get_db
from ..api.auth import get_current_user

router = APIRouter()

@router.get("/")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    db = get_db()
    notifs = await db.notifications.find({"user_id": ObjectId(current_user["_id"]), "read": False}).sort("created_at", -1).to_list(20)
    for n in notifs:
        n["_id"] = str(n["_id"])
        n["user_id"] = str(n["user_id"])
    return notifs

@router.post("/mark-read")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    db = get_db()
    await db.notifications.update_many({"user_id": ObjectId(current_user["_id"])}, {"$set": {"read": True}})
    return {"message": "Marked all as read"}

@router.post("/subscribe")
async def subscribe_push(subscription: dict, current_user: dict = Depends(get_current_user)):
    db = get_db()
    await db.users.update_one({"_id": ObjectId(current_user["_id"])}, {"$set": {"push_subscription": subscription}})
    return {"message": "Subscribed"}
