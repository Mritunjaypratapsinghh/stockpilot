from fastapi import APIRouter, Depends
from beanie import PydanticObjectId

from ..models.documents import Notification, User
from ..api.auth import get_current_user

router = APIRouter()


@router.get("/")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifs = await Notification.find(
        Notification.user_id == PydanticObjectId(current_user["_id"]),
        Notification.read == False
    ).sort(-Notification.created_at).limit(20).to_list()
    return [{"_id": str(n.id), "user_id": str(n.user_id), "title": n.title, "message": n.message, "created_at": n.created_at} for n in notifs]


@router.post("/mark-read")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    await Notification.find(Notification.user_id == PydanticObjectId(current_user["_id"])).update_many({"$set": {"read": True}})
    return {"message": "Marked all as read"}


@router.post("/subscribe")
async def subscribe_push(subscription: dict, current_user: dict = Depends(get_current_user)):
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if user:
        user.push_subscription = subscription
        await user.save()
    return {"message": "Subscribed"}
