from fastapi import APIRouter

from .auth import router as auth_router
from .portfolio import router as portfolio_router
from .market import router as market_router
from .alerts import router as alerts_router
from .watchlist import router as watchlist_router
from .finance import router as finance_router
from .analytics import router as analytics_router
from .ipo import router as ipo_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(watchlist_router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(finance_router, prefix="/finance", tags=["finance"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ipo_router, prefix="/ipo", tags=["ipo"])
