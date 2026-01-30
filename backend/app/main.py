from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from .core.database import init_db, close_db
from .utils.logger import logger
from .api import auth, portfolio, alerts, market
from .api import research, ipo, transactions, watchlist, notifications
from .api import import_holdings, dividends, export
from .api import goals, tax, analytics
from .api import screener, sip, corporate_actions, compare, rebalance
from .api import networth, pnl_calendar, mf_health
from .tasks.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting StockPilot API...")
    await init_db()
    start_scheduler()
    logger.info("StockPilot API ready")
    yield
    logger.info("Shutting down...")
    await close_db()

app = FastAPI(
    title="StockPilot API",
    description="Personal Portfolio Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration}ms)")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(market.router, prefix="/api/market", tags=["Market Data"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(ipo.router, prefix="/api/ipo", tags=["IPO"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(import_holdings.router, prefix="/api/portfolio", tags=["Import"])
app.include_router(dividends.router, prefix="/api/dividends", tags=["Dividends"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(goals.router, prefix="/api/goals", tags=["Goals"])
app.include_router(tax.router, prefix="/api/tax", tags=["Tax"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(screener.router, prefix="/api/screener", tags=["Screener"])
app.include_router(sip.router, prefix="/api/sip", tags=["SIP"])
app.include_router(corporate_actions.router, prefix="/api/corporate-actions", tags=["Corporate Actions"])
app.include_router(compare.router, prefix="/api/compare", tags=["Compare"])
app.include_router(rebalance.router, prefix="/api/rebalance", tags=["Rebalance"])
app.include_router(networth.router, prefix="/api/networth", tags=["Net Worth"])
app.include_router(pnl_calendar.router, prefix="/api/pnl", tags=["P&L Calendar"])
app.include_router(mf_health.router, prefix="/api/mf", tags=["MF Health"])

@app.get("/")
async def root():
    return {"message": "StockPilot API", "version": "0.1.0"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "healthy"}
