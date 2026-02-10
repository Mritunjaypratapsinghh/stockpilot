"""API module - exports v1 routers"""

from .v1 import router as v1_router
from .v1.alerts import router as alerts_router
from .v1.analytics import router as analytics_router
from .v1.auth import router as auth_router
from .v1.finance import router as finance_router
from .v1.ipo import router as ipo_router
from .v1.market import router as market_router
from .v1.portfolio import router as portfolio_router
from .v1.watchlist import router as watchlist_router

__all__ = [
    "v1_router",
    "auth_router",
    "portfolio_router",
    "market_router",
    "alerts_router",
    "finance_router",
    "analytics_router",
    "ipo_router",
    "watchlist_router",
]
