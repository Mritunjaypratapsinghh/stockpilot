"""API v1 module"""
from fastapi import APIRouter

from .auth import router as auth_router
from .portfolio import router as portfolio_router
from .market import router as market_router
from .alerts import router as alerts_router
from .finance import router as finance_router
from .analytics import router as analytics_router
from .ipo import router as ipo_router
from .watchlist import router as watchlist_router

# Create v1 router
router = APIRouter(prefix="/v1")

# Include all routers
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio"])
router.include_router(market_router, prefix="/market", tags=["Market"])
router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
router.include_router(finance_router, prefix="/finance", tags=["Finance"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
router.include_router(ipo_router, prefix="/ipo", tags=["IPO"])
router.include_router(watchlist_router, prefix="/watchlist", tags=["Watchlist"])

__all__ = ["router"]
