"""Analytics module - analytics, pnl_calendar, networth, rebalance"""
from fastapi import APIRouter

from ...analytics import router as analytics_router
from ...pnl_calendar import router as pnl_router
from ...networth import router as networth_router
from ...rebalance import router as rebalance_router

router = APIRouter()
router.include_router(analytics_router, prefix="", tags=["analytics"])
router.include_router(pnl_router, prefix="/pnl", tags=["pnl"])
router.include_router(networth_router, prefix="/networth", tags=["networth"])
router.include_router(rebalance_router, prefix="/rebalance", tags=["rebalance"])
