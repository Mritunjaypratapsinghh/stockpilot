from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, date, timezone
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, Literal

from ..models.documents import Goal, Holding
from ..models.documents.goal import Contribution
from ..api.auth import get_current_user

router = APIRouter()


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
    user_id = PydanticObjectId(current_user["_id"])
    goals = await Goal.find(Goal.user_id == user_id).to_list()
    holdings = await Holding.find(Holding.user_id == user_id).to_list()
    portfolio_value = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings)

    result = []
    for g in goals:
        target = g.target_amount
        current = g.current_value
        progress = (current / target * 100) if target > 0 else 0

        target_date = datetime.fromisoformat(g.target_date).date() if isinstance(g.target_date, str) else g.target_date
        months_left = max(0, (target_date.year - datetime.now().year) * 12 + (target_date.month - datetime.now().month))

        remaining = target - current
        if months_left > 0 and remaining > 0:
            r = 0.12 / 12
            required_sip = remaining * r / ((1 + r) ** months_left - 1)
        else:
            required_sip = remaining if remaining > 0 else 0

        result.append({
            "_id": str(g.id), "name": g.name, "category": g.category, "target_amount": target,
            "current_value": current, "progress": round(progress, 1), "target_date": g.target_date,
            "months_left": months_left, "monthly_sip": g.monthly_sip, "required_sip": round(required_sip, 0),
            "on_track": g.monthly_sip >= required_sip if required_sip > 0 else True
        })

    return {"goals": result, "portfolio_value": round(portfolio_value, 2)}


@router.post("/")
async def create_goal(goal: GoalCreate, current_user: dict = Depends(get_current_user)):
    doc = Goal(
        user_id=PydanticObjectId(current_user["_id"]),
        name=goal.name.strip(),
        category=goal.category,
        target_amount=goal.target_amount,
        target_date=goal.target_date.isoformat(),
        monthly_sip=goal.monthly_sip or 0
    )
    await doc.insert()
    return {"message": "Goal created", "id": str(doc.id)}


@router.put("/{goal_id}")
async def update_goal(goal_id: str, goal: GoalUpdate, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(goal_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    g = await Goal.find_one(Goal.id == PydanticObjectId(goal_id), Goal.user_id == PydanticObjectId(current_user["_id"]))
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")

    updates = goal.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    for k, v in updates.items():
        setattr(g, k, v.isoformat() if isinstance(v, date) else v)
    await g.save()
    return {"message": "Goal updated"}


@router.delete("/{goal_id}")
async def delete_goal(goal_id: str, current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(goal_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    g = await Goal.find_one(Goal.id == PydanticObjectId(goal_id), Goal.user_id == PydanticObjectId(current_user["_id"]))
    if g:
        await g.delete()
    return {"message": "Goal deleted"}


@router.post("/{goal_id}/contribute")
async def add_contribution(goal_id: str, amount: float = Query(..., gt=0), current_user: dict = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(goal_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    g = await Goal.find_one(Goal.id == PydanticObjectId(goal_id), Goal.user_id == PydanticObjectId(current_user["_id"]))
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")

    g.current_value += amount
    g.contributions.append(Contribution(amount=amount, date=datetime.now(timezone.utc).isoformat()))
    await g.save()
    return {"message": "Contribution added"}


@router.get("/projections")
async def get_projections(current_user: dict = Depends(get_current_user)):
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(current_user["_id"])).to_list()
    current_value = sum(h.quantity * (h.current_price or h.avg_price) for h in holdings)

    projections = [{"years": y, "conservative": round(current_value * (1.08 ** y), 0), "moderate": round(current_value * (1.12 ** y), 0), "aggressive": round(current_value * (1.15 ** y), 0)} for y in [1, 3, 5, 10]]
    return {"current_value": round(current_value, 0), "projections": projections}
