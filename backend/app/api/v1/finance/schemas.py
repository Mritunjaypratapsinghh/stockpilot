"""Finance schemas"""
from pydantic import BaseModel, Field
from typing import Literal


# Request schemas
class GoalCreate(BaseModel):
    name: str
    target_amount: float = Field(..., gt=0)
    target_date: str
    current_amount: float = 0


class SIPCreate(BaseModel):
    symbol: str
    amount: float = Field(..., gt=0)
    frequency: Literal["monthly", "weekly", "quarterly"] = "monthly"
    sip_date: int = Field(1, ge=1, le=28)


# Response schemas
class GoalResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    target_amount: float
    current_amount: float
    target_date: str
    progress: float


class SIPResponse(BaseModel):
    id: str = Field(alias="_id")
    symbol: str
    amount: float
    frequency: str
    sip_date: int
    is_active: bool


class TaxSummary(BaseModel):
    ltcg: float
    stcg: float
    ltcg_taxable: float
    ltcg_tax: float
    stcg_tax: float
    total_tax: float


class NetworthSummary(BaseModel):
    total: float


class AssetCreate(BaseModel):
    name: str
    category: str
    value: float = Field(..., gt=0)


class AssetUpdate(BaseModel):
    name: str
    category: str
    value: float = Field(..., gt=0)


class NetworthSnapshot(BaseModel):
    date: str
    total: float
    breakdown: dict[str, float] = {}


class ImportHistory(BaseModel):
    snapshots: list[NetworthSnapshot]
