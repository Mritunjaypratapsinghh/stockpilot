# Portfolio module - aggregates portfolio, transactions, import_holdings, mf_health
from fastapi import APIRouter

from ...portfolio import router as portfolio_router
from ...transactions import router as transactions_router
from ...import_holdings import router as import_router
from ...mf_health import router as mf_router

router = APIRouter()
router.include_router(portfolio_router, tags=["portfolio"])
router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
router.include_router(import_router, tags=["import"])
router.include_router(mf_router, prefix="/mf", tags=["mf-health"])
