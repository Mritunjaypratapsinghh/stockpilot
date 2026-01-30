# Market module - aggregates market, research, screener, compare, corporate_actions
from fastapi import APIRouter

from ...market import router as market_router
from ...research import router as research_router
from ...screener import router as screener_router
from ...compare import router as compare_router
from ...corporate_actions import router as corporate_router

router = APIRouter()
router.include_router(market_router, tags=["market"])
router.include_router(research_router, prefix="/research", tags=["research"])
router.include_router(screener_router, prefix="/screener", tags=["screener"])
router.include_router(compare_router, prefix="/compare", tags=["compare"])
router.include_router(corporate_router, prefix="/corporate-actions", tags=["corporate-actions"])
