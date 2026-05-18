"""Prometheus metrics — request latency, error rates, cache hits, active connections."""

import time

from fastapi import Request
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# ── Metrics ──
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint", "status"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
ACTIVE_REQUESTS = Gauge("http_active_requests", "Currently active requests")
ERROR_COUNT = Counter("http_errors_total", "Total HTTP errors (4xx/5xx)", ["method", "endpoint", "status"])
CACHE_HIT = Counter("cache_hits_total", "Cache hits")
CACHE_MISS = Counter("cache_misses_total", "Cache misses")
WS_CONNECTIONS = Gauge("websocket_active_connections", "Active WebSocket connections")
SCHEDULER_RUNS = Counter("scheduler_job_runs_total", "Scheduler job executions", ["job_id", "status"])


def _normalize_path(path: str) -> str:
    """Collapse path params to reduce cardinality: /api/portfolio/holdings/abc123 → /api/portfolio/holdings/{id}"""
    parts = path.strip("/").split("/")
    normalized = []
    for p in parts:
        if len(p) == 24 and all(c in "0123456789abcdef" for c in p):
            normalized.append("{id}")
        elif p.replace("-", "").isdigit():
            normalized.append("{id}")
        else:
            normalized.append(p)
    return "/" + "/".join(normalized)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return Response(content=generate_latest(), media_type="text/plain")

        ACTIVE_REQUESTS.inc()
        start = time.time()
        try:
            response = await call_next(request)
        except Exception:
            ACTIVE_REQUESTS.dec()
            raise

        duration = time.time() - start
        path = _normalize_path(request.url.path)
        method = request.method
        status = str(response.status_code)

        REQUEST_LATENCY.labels(method, path, status).observe(duration)
        REQUEST_COUNT.labels(method, path, status).inc()
        if response.status_code >= 400:
            ERROR_COUNT.labels(method, path, status).inc()
        ACTIVE_REQUESTS.dec()

        return response
