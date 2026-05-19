"""
CSRF protection middleware.

Strategy: Double-submit cookie pattern.
- On first request, set a CSRF token cookie (readable by JS, NOT httpOnly).
- Frontend reads it and sends it back as X-CSRF-Token header on POST/PUT/DELETE.
- Backend verifies header matches cookie.

This protects against cross-origin form submissions while allowing our SPA to work.
"""

import secrets

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
EXEMPT_PATHS = {"/api/auth/login", "/api/auth/register", "/api/auth/google", "/api/auth/logout", "/health", "/metrics"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Set CSRF cookie if not present
        csrf_cookie = request.cookies.get(CSRF_COOKIE)
        if not csrf_cookie:
            csrf_cookie = secrets.token_hex(16)

        # Verify on state-changing methods
        if request.method not in SAFE_METHODS and request.url.path not in EXEMPT_PATHS:
            csrf_header = request.headers.get(CSRF_HEADER, "")
            if not csrf_cookie or csrf_header != csrf_cookie:
                raise HTTPException(status_code=403, detail="CSRF token missing or invalid")

        response = await call_next(request)

        # Always set/refresh the CSRF cookie (JS-readable, not httpOnly)
        response.set_cookie(
            key=CSRF_COOKIE,
            value=csrf_cookie,
            httponly=False,  # Must be readable by frontend JS
            secure=True,
            samesite="none",
            path="/",
            max_age=86400,
        )
        return response
