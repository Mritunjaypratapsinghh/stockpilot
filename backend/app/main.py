from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from .core.database import init_db, close_db
from .core.config import settings
from .utils.logger import logger
from .api.v1 import router as v1_router
from .api.v1.auth import router as auth_router
from .api.v1.portfolio import router as portfolio_router
from .api.v1.market import router as market_router
from .api.v1.alerts import router as alerts_router
from .api.v1.finance import router as finance_router
from .api.v1.analytics import router as analytics_router
from .api.v1.ipo import router as ipo_router
from .api.v1.watchlist import router as watchlist_router
from .tasks.scheduler import start_scheduler


# CORS origins - restrict in production
CORS_ORIGINS = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
    "https://stockpilot-psi.vercel.app"
]
if settings.cors_origins:
    CORS_ORIGINS.extend(settings.cors_origins.split(","))


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
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({round((time.time() - start) * 1000)}ms)")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# V1 API routes (new structure)
app.include_router(v1_router, prefix="/api")

# Legacy routes (backward compatibility with frontend using /api/* paths)
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(market_router, prefix="/api/market", tags=["Market"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ipo_router, prefix="/api/ipo", tags=["IPO"])
app.include_router(watchlist_router, prefix="/api/watchlist", tags=["Watchlist"])


@app.get("/")
async def root():
    return {"message": "StockPilot API", "version": "1.0.0"}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "healthy"}
