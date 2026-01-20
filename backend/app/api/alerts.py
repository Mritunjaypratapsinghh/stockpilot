from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from bson import ObjectId
from ..database import get_db
from ..api.auth import get_current_user
from ..models import Alert, AlertCreate

router = APIRouter()

@router.get("")
@router.get("/")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    db = get_db()
    alerts = await db.alerts.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    for a in alerts:
        a["_id"] = str(a["_id"])
        a["user_id"] = str(a["user_id"])
    return alerts

@router.post("/")
async def create_alert(alert: AlertCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    doc = {
        "user_id": ObjectId(current_user["_id"]),
        "symbol": alert.symbol.upper(),
        "alert_type": alert.alert_type,
        "target_value": alert.target_value,
        "is_active": True,
        "triggered_at": None,
        "notification_sent": False,
        "created_at": datetime.utcnow()
    }
    result = await db.alerts.insert_one(doc)
    return {"_id": str(result.inserted_id), "symbol": doc["symbol"], "alert_type": doc["alert_type"], "target_value": doc["target_value"], "is_active": True}

@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    result = await db.alerts.delete_one({"_id": ObjectId(alert_id), "user_id": ObjectId(current_user["_id"])})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Deleted successfully"}

@router.put("/{alert_id}/toggle")
async def toggle_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    alert = await db.alerts.find_one({"_id": ObjectId(alert_id), "user_id": ObjectId(current_user["_id"])})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.alerts.update_one({"_id": ObjectId(alert_id)}, {"$set": {"is_active": not alert["is_active"]}})
    return {"message": "Toggled successfully", "is_active": not alert["is_active"]}
