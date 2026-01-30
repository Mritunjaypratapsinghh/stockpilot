from fastapi import APIRouter, HTTPException, Depends
from beanie import PydanticObjectId

from ..models.documents import Alert
from ..models import AlertCreate
from ..api.auth import get_current_user

router = APIRouter()


@router.get("")
@router.get("/")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    alerts = await Alert.find(Alert.user_id == PydanticObjectId(current_user["_id"])).to_list()
    return [{"_id": str(a.id), "user_id": str(a.user_id), "symbol": a.symbol, "alert_type": a.alert_type, "target_value": a.target_value, "is_active": a.is_active} for a in alerts]


@router.post("/")
async def create_alert(alert: AlertCreate, current_user: dict = Depends(get_current_user)):
    doc = Alert(
        user_id=PydanticObjectId(current_user["_id"]),
        symbol=alert.symbol.strip().upper(),
        alert_type=alert.alert_type,
        target_value=alert.target_value
    )
    await doc.insert()
    return {"_id": str(doc.id), "symbol": doc.symbol, "alert_type": doc.alert_type, "target_value": doc.target_value, "is_active": True}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    alert = await Alert.find_one(Alert.id == PydanticObjectId(alert_id), Alert.user_id == PydanticObjectId(current_user["_id"]))
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await alert.delete()
    return {"message": "Deleted successfully"}


@router.put("/{alert_id}/toggle")
async def toggle_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    alert = await Alert.find_one(Alert.id == PydanticObjectId(alert_id), Alert.user_id == PydanticObjectId(current_user["_id"]))
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = not alert.is_active
    await alert.save()
    return {"message": "Toggled successfully", "is_active": alert.is_active}
