"""Alerts routes - alerts and notifications."""

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from ....core.response_handler import StandardResponse
from ....core.security import get_current_user
from ....models.documents import Alert, Notification, User
from .schemas import AlertCreate, AlertResponse, NotificationResponse, PushSubscription

router = APIRouter()


@router.get("", summary="Get alerts", description="List all price alerts")
async def get_alerts(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get all price alerts for user."""
    alerts = await Alert.find(Alert.user_id == PydanticObjectId(current_user["_id"])).to_list()
    return StandardResponse.ok(
        [
            AlertResponse(
                _id=str(a.id),
                symbol=a.symbol,
                alert_type=a.alert_type,
                target_value=a.target_value,
                is_active=a.is_active,
            )
            for a in alerts
        ]
    )


@router.post("/", summary="Create alert", description="Create a new price alert")
async def create_alert(alert: AlertCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Create a new price alert."""
    doc = Alert(
        user_id=PydanticObjectId(current_user["_id"]),
        symbol=alert.symbol.upper(),
        alert_type=alert.alert_type,
        target_value=alert.target_value,
    )
    await doc.insert()
    return StandardResponse.ok(
        AlertResponse(
            _id=str(doc.id), symbol=doc.symbol, alert_type=doc.alert_type, target_value=doc.target_value, is_active=True
        ),
        "Alert created",
    )


@router.delete("/{alert_id}", summary="Delete alert", description="Delete a price alert")
async def delete_alert(alert_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Delete a price alert."""
    if not PydanticObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    alert = await Alert.find_one(
        Alert.id == PydanticObjectId(alert_id), Alert.user_id == PydanticObjectId(current_user["_id"])
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await alert.delete()
    return StandardResponse.ok(message="Alert deleted")


@router.put("/{alert_id}/toggle", summary="Toggle alert", description="Enable or disable an alert")
async def toggle_alert(alert_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Toggle alert active status."""
    if not PydanticObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    alert = await Alert.find_one(
        Alert.id == PydanticObjectId(alert_id), Alert.user_id == PydanticObjectId(current_user["_id"])
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = not alert.is_active
    await alert.save()
    return StandardResponse.ok({"is_active": alert.is_active})


@router.get("/notifications", summary="Get notifications", description="Get unread notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Get unread notifications."""
    notifs = (
        await Notification.find(
            Notification.user_id == PydanticObjectId(current_user["_id"]),
            Notification.read == False,  # noqa: E712
        )
        .sort(-Notification.created_at)
        .limit(20)
        .to_list()
    )
    return StandardResponse.ok(
        [NotificationResponse(_id=str(n.id), title=n.title, message=n.message, created_at=n.created_at) for n in notifs]
    )


@router.post("/notifications/mark-read", summary="Mark all read", description="Mark all notifications as read")
async def mark_all_read(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    """Mark all notifications as read."""
    await Notification.find(Notification.user_id == PydanticObjectId(current_user["_id"])).update_many(
        {"$set": {"read": True}}
    )
    return StandardResponse.ok(message="Marked all as read")


@router.post("/notifications/subscribe", summary="Subscribe to push", description="Subscribe to web push notifications")
async def subscribe_push(
    subscription: PushSubscription, current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    """Subscribe to push notifications."""
    user = await User.get(PydanticObjectId(current_user["_id"]))
    if user:
        user.push_subscription = subscription.model_dump()
        await user.save()
    return StandardResponse.ok(message="Subscribed")
