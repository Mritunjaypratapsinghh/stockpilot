"""Finance module - tax, dividends, goals, sip"""
from fastapi import APIRouter

from ...tax import router as tax_router
from ...dividends import router as dividends_router
from ...goals import router as goals_router
from ...sip import router as sip_router

router = APIRouter()
router.include_router(tax_router, prefix="/tax", tags=["tax"])
router.include_router(dividends_router, prefix="/dividends", tags=["dividends"])
router.include_router(goals_router, prefix="/goals", tags=["goals"])
router.include_router(sip_router, prefix="/sip", tags=["sip"])
