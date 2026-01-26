from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, date, timezone
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, Literal
from ..database import get_db
from ..api.auth import get_current_user

router = APIRouter()

def validate_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return ObjectId(id_str)

class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    target_date: date
    category: Literal["retirement", "house", "education", "emergency", "general"] = "general"
    monthly_sip: Optional[float] = Field(None, ge=0)

class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[date] = None
    monthly_sip: Optional[float] = Field(None, ge=0)

@router.get("/")
async def get_goals(current_user: dict = Depends(get_current_user)):
    db = get_db()
    goals = await db.goals.find({"user_id": ObjectId(current_user["_id"])}).to_list(50)
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    portfolio_value = sum(h["quantity"] * h.get("current_price", h["avg_price"]) for h in holdings)
    
    result = []
    for g in goals:
        target = g["target_amount"]
        current = g.get("current_value", 0)
        progress = (current / target * 100) if target > 0 else 0
        
        target_date = g["target_date"] if isinstance(g["target_date"], date) else datetime.fromisoformat(g["target_date"]).date()
        months_left = max(0, (target_date.year - datetime.now().year) * 12 + (target_date.month - datetime.now().month))
        
        remaining = target - current
        if months_left > 0 and remaining > 0:
            r = 0.12 / 12
            required_sip = remaining * r / ((1 + r) ** months_left - 1)
        else:
            required_sip = remaining if remaining > 0 else 0
        
        result.append({
            "_id": str(g["_id"]),
            "name": g["name"],
            "category": g.get("category", "general"),
            "target_amount": target,
            "current_value": current,
            "progress": round(progress, 1),
            "target_date": g["target_date"],
            "months_left": months_left,
            "monthly_sip": g.get("monthly_sip", 0),
            "required_sip": round(required_sip, 0),
            "on_track": g.get("monthly_sip", 0) >= required_sip if required_sip > 0 else True
        })
    
    return {"goals": result, "portfolio_value": round(portfolio_value, 2)}

@router.post("/")
async def create_goal(goal: GoalCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    doc = {
        "user_id": ObjectId(current_user["_id"]),
        "name": goal.name.strip(),
        "category": goal.category,
        "target_amount": goal.target_amount,
        "target_date": goal.target_date.isoformat(),
        "current_value": 0,
        "monthly_sip": goal.monthly_sip or 0,
        "contributions": [],
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.goals.insert_one(doc)
    return {"message": "Goal created", "id": str(result.inserted_id)}

@router.put("/{goal_id}")
async def update_goal(goal_id: str, goal: GoalUpdate, current_user: dict = Depends(get_current_user)):
    oid = validate_object_id(goal_id)
    db = get_db()
    update = {k: v.isoformat() if isinstance(v, date) else v for k, v in goal.model_dump(exclude_none=True).items()}
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.goals.update_one({"_id": oid, "user_id": ObjectId(current_user["_id"])}, {"$set": update})
    return {"message": "Goal updated"}

@router.delete("/{goal_id}")
async def delete_goal(goal_id: str, current_user: dict = Depends(get_current_user)):
    oid = validate_object_id(goal_id)
    db = get_db()
    await db.goals.delete_one({"_id": oid, "user_id": ObjectId(current_user["_id"])})
    return {"message": "Goal deleted"}

@router.post("/{goal_id}/contribute")
async def add_contribution(goal_id: str, amount: float = Query(..., gt=0), current_user: dict = Depends(get_current_user)):
    oid = validate_object_id(goal_id)
    db = get_db()
    contribution = {"amount": amount, "date": datetime.now(timezone.utc).isoformat()}
    await db.goals.update_one(
        {"_id": oid, "user_id": ObjectId(current_user["_id"])},
        {"$inc": {"current_value": amount}, "$push": {"contributions": contribution}}
    )
    return {"message": "Contribution added"}

@router.get("/projections")
async def get_projections(current_user: dict = Depends(get_current_user)):
    db = get_db()
    holdings = await db.holdings.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
    current_value = sum(h["quantity"] * h.get("current_price", h["avg_price"]) for h in holdings)
    
    projections = [{"years": y, "conservative": round(current_value * (1.08 ** y), 0), "moderate": round(current_value * (1.12 ** y), 0), "aggressive": round(current_value * (1.15 ** y), 0)} for y in [1, 3, 5, 10]]
    return {"current_value": round(current_value, 0), "projections": projections}
