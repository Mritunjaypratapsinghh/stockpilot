"""
Test configuration — fixtures, factories, and shared utilities.

Provides:
- Async test client (no real DB needed for unit tests)
- User factories
- Token generators
- Holding factories
- Freezegun-compatible date helpers
"""

from datetime import date, datetime, timezone

import pytest
from app.core.security import create_access_token
from beanie import PydanticObjectId

# ── Factories ──


def make_user_id() -> str:
    """Generate a realistic MongoDB ObjectId string."""
    return str(PydanticObjectId())


def make_token(user_id: str = None, email: str = "test@example.com", expired: bool = False) -> str:
    """Generate a valid JWT token for testing."""
    uid = user_id or make_user_id()
    if expired:

        from app.core.config import settings
        from jose import jwt

        payload = {"sub": uid, "email": email, "exp": datetime(2020, 1, 1, tzinfo=timezone.utc)}
        return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return create_access_token({"sub": uid}, email=email)


def make_holding(
    symbol: str = "TCS",
    quantity: float = 10,
    avg_price: float = 3500,
    holding_type: str = "EQUITY",
    transactions: list = None,
) -> dict:
    """Factory for holding data."""
    return {
        "symbol": symbol,
        "name": symbol,
        "exchange": "NSE",
        "holding_type": holding_type,
        "quantity": quantity,
        "avg_price": avg_price,
        "current_price": avg_price * 1.1,
        "transactions": transactions or [],
    }


def make_transaction(
    txn_type: str = "BUY", quantity: float = 10, price: float = 3500, date_str: str = "2024-01-15"
) -> dict:
    """Factory for transaction data."""
    return {"type": txn_type, "quantity": quantity, "price": price, "date": date_str}


def make_ais_item(info_code: str = "192", amount: int = 50000, status: str = "pending", category: str = "TDS") -> dict:
    """Factory for AIS line item."""
    return {
        "info_code": info_code,
        "description": f"TDS u/s {info_code}",
        "source_name": "Test Corp",
        "source_tan": "ABCD12345E",
        "reported_value": amount,
        "category": category,
        "status": status,
    }


# ── Auth Fixtures ──


@pytest.fixture
def user_id() -> str:
    return make_user_id()


@pytest.fixture
def auth_token(user_id) -> str:
    return make_token(user_id)


@pytest.fixture
def auth_headers(auth_token) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def expired_token() -> str:
    return make_token(expired=True)


@pytest.fixture
def malformed_token() -> str:
    return "not.a.valid.jwt.token"


# ── Date Fixtures ──


@pytest.fixture
def fy_2025_26():
    """FY 2025-26 boundaries."""
    return {"fy": "2025-26", "start": date(2025, 4, 1), "end": date(2026, 3, 31)}


@pytest.fixture
def fy_boundary_dates():
    """Edge case dates around FY boundaries."""
    return {
        "last_day_prev_fy": date(2025, 3, 31),
        "first_day_curr_fy": date(2025, 4, 1),
        "last_day_curr_fy": date(2026, 3, 31),
        "first_day_next_fy": date(2026, 4, 1),
    }
