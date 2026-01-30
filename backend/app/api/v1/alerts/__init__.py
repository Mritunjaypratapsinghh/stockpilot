# Alerts module - aggregates alerts, notifications
from fastapi import APIRouter

from ...alerts import router as alerts_router
from ...notifications import router as notifications_router

router = APIRouter()
router.include_router(alerts_router, tags=["alerts"])
router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
