import time
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.v1 import router as v1_router
from .core.config import settings
from .core.database import close_db, init_db
from .core.security import verify_token
from .middleware.correlation import CorrelationIDMiddleware
from .middleware.csrf import CSRFMiddleware
from .middleware.metrics import PrometheusMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware
from .services.cache import close_redis, get_redis
from .services.http_client import close_http_client
from .services.market.price_service import get_bulk_prices
from .services.websocket import ws_manager
from .tasks.scheduler import start_scheduler
from .utils.logger import logger

# Sentry error tracking
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1, profiles_sample_rate=0.1)

# CORS origins - restrict in production
CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "https://stockpilot-psi.vercel.app"]
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
    await close_http_client()
    await close_redis()
    await close_db()


app = FastAPI(
    title="StockPilot API",
    description="Personal Portfolio Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = round((time.time() - start) * 1000)
    path = request.url.path
    logger.info(f"{request.method} {path} - {response.status_code} ({ms}ms)")

    # Track API usage in Redis for analytics
    if path.startswith("/api/") and response.status_code < 400:
        try:
            redis = await get_redis()
            if redis:
                today = time.strftime("%Y-%m-%d")
                ep_key = f"analytics:endpoints:{today}"
                dau_key = f"analytics:dau:{today}"
                await redis.hincrby(ep_key, path, 1)
                await redis.expire(ep_key, 7 * 86400)  # 7 days TTL
                auth = request.headers.get("authorization", "")
                if auth.startswith("Bearer "):
                    user = verify_token(auth.split(" ")[1])
                    if user:
                        await redis.sadd(dau_key, user["_id"])
                        await redis.expire(dau_key, 7 * 86400)
        except Exception:
            pass

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(CSRFMiddleware)

# All API routes
app.include_router(health_router)
app.include_router(v1_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "StockPilot API", "version": "1.0.0"}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    """Health check with dependency verification."""
    checks = {"api": "healthy"}

    # Check MongoDB
    try:
        from .core.database import client

        if client:
            await client.admin.command("ping")
            checks["mongodb"] = "healthy"
        else:
            checks["mongodb"] = "not_connected"
    except Exception:
        checks["mongodb"] = "unhealthy"

    # Check Redis
    try:
        redis = await get_redis()
        if redis:
            await redis.ping()
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "unavailable"
    except Exception:
        checks["redis"] = "unhealthy"

    status = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for real-time price updates. Requires valid JWT."""
    # Authenticate: check token query param or cookie
    user = None
    if token:
        user = verify_token(token)
    if not user:
        # Try cookie
        cookie_token = websocket.cookies.get("access_token")
        if cookie_token:
            user = verify_token(cookie_token)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    user_id = user["_id"]
    await ws_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            symbols = data.get("symbols", [])

            if action == "subscribe" and symbols:
                symbols = symbols[:50]  # Limit to prevent abuse
                await ws_manager.subscribe(user_id, symbols)
                prices = await get_bulk_prices(symbols)
                for symbol, price_data in prices.items():
                    await websocket.send_json({"type": "price", "symbol": symbol, "data": price_data})
            elif action == "unsubscribe" and symbols:
                await ws_manager.unsubscribe(user_id, symbols)

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket, user_id)
