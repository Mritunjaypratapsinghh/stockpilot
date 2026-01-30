# Backend Code Review

**Date:** 2026-01-31  
**Reviewer:** AI Code Review  
**Branch:** refactor-backend  
**Scope:** Full backend codebase analysis

---

## Executive Summary

| Category | Score | Status |
|----------|-------|--------|
| **Architecture** | 7/10 | ⚠️ Needs Improvement |
| **PEP8 Compliance** | 6/10 | ⚠️ Needs Improvement |
| **Design Patterns** | 6/10 | ⚠️ Needs Improvement |
| **Error Handling** | 4/10 | ❌ Critical |
| **Security** | 7/10 | ⚠️ Needs Improvement |
| **Code Quality** | 6/10 | ⚠️ Needs Improvement |
| **Documentation** | 3/10 | ❌ Critical |
| **Testing** | 0/10 | ❌ Critical |

**Overall Score: 5.5/10**

---

## 1. Architecture Issues

### 1.1 ❌ Duplicate Code (DRY Violation)

**Severity: HIGH**

Multiple files contain identical functions:

```python
# Duplicated in: portfolio.py, analytics.py, export.py, tax.py
async def get_user_holdings(user_id: str):
    return await Holding.find(Holding.user_id == PydanticObjectId(user_id)).to_list()

async def get_prices_for_holdings(holdings):
    symbols = [h.symbol for h in holdings if h.holding_type != "MF"]
    return await get_bulk_prices(symbols) if symbols else {}
```

**Files affected:**
- `api/portfolio.py`
- `api/analytics.py`
- `api/export.py`
- `api/tax.py`
- `api/networth.py`

**Recommendation:** Extract to `services/portfolio/service.py`

### 1.2 ❌ Duplicate Service Files

**Severity: MEDIUM**

Services exist in both root and subdirectories:
- `services/price_service.py` AND `services/market/price_service.py`
- `services/notification_service.py` AND `services/notification/service.py`
- `services/enhanced_analysis.py` AND `services/analytics/service.py`
- `services/multi_source_price.py` AND `services/market/multi_source_price.py`

**Recommendation:** Remove root-level duplicates, keep only subdirectory versions.

### 1.3 ⚠️ Duplicate Auth Functions

**Severity: MEDIUM**

`get_current_user`, `hash_password`, `verify_password`, `create_access_token` exist in:
- `api/auth.py`
- `core/security.py`

**Recommendation:** Use only `core/security.py`, update all imports.

### 1.4 ⚠️ SECTOR_MAP Hardcoded in Route File

**Severity: MEDIUM**

```python
# api/portfolio.py - Line 11-26
SECTOR_MAP = {
    "RELIANCE": "Oil & Gas", "ONGC": "Oil & Gas", ...
}
```

**Recommendation:** Already exists in `core/constants.py`. Import from there.

### 1.5 ⚠️ Business Logic in Route Handlers

**Severity: MEDIUM**

Route handlers contain business logic instead of delegating to services:

```python
# api/portfolio.py - XIRR calculation in route handler
@router.get("/xirr")
async def get_portfolio_xirr(current_user: dict = Depends(get_current_user)):
    # 50+ lines of XIRR calculation logic
    def xnpv(rate, cfs):
        ...
```

**Recommendation:** Extract to `services/portfolio/xirr_service.py`

---

## 2. PEP8 & Style Violations

### 2.1 ❌ Line Length Violations

**Severity: MEDIUM**

Multiple lines exceed 79/120 characters:

```python
# api/portfolio.py - Line 12-26 (SECTOR_MAP)
"HDFCBANK": "Banking", "ICICIBANK": "Banking", "KOTAKBANK": "Banking", "AXISBANK": "Banking", ...
```

**Recommendation:** Use multi-line formatting:
```python
SECTOR_MAP = {
    "RELIANCE": "Oil & Gas",
    "ONGC": "Oil & Gas",
    ...
}
```

### 2.2 ⚠️ Missing Type Hints

**Severity: LOW**

Many functions lack return type hints:

```python
# Bad
async def get_user_holdings(user_id: str):
    return await Holding.find(...).to_list()

# Good
async def get_user_holdings(user_id: str) -> List[Holding]:
    return await Holding.find(...).to_list()
```

**Files affected:** Most API route files

### 2.3 ⚠️ Inconsistent Naming

**Severity: LOW**

Mixed naming conventions:
- `get_current_user` vs `get_me` (function names)
- `holding_id` vs `alert_id` vs `goal_id` (parameter names - consistent ✓)
- `HoldingCreate` vs `GoalCreate` (schema names - consistent ✓)

### 2.4 ⚠️ Missing Blank Lines

**Severity: LOW**

PEP8 requires 2 blank lines between top-level definitions:

```python
# Bad (api/alerts.py)
router = APIRouter()
@router.get("")

# Good
router = APIRouter()


@router.get("")
```

---

## 3. Error Handling Issues

### 3.1 ❌ Bare Except Clauses

**Severity: CRITICAL**

**74 instances** of poor exception handling found:

```python
# Bad - Silently swallows all exceptions
except:
    pass

# Bad - Catches everything including SystemExit, KeyboardInterrupt
except Exception as e:
    print(f"Error: {e}")
```

**Files with bare `except:`:**
- `api/research.py` (7 instances)
- `tasks/ipo_tracker.py` (5 instances)
- `api/ipo.py` (5 instances)
- `api/import_holdings.py` (4 instances)
- `api/portfolio.py` (2 instances)
- `tasks/alert_checker.py` (1 instance)
- `tasks/earnings_checker.py` (1 instance)

**Recommendation:**
```python
# Good - Specific exception handling
except httpx.HTTPError as e:
    logger.error(f"HTTP error fetching {symbol}: {e}")
    return None
except ValueError as e:
    logger.warning(f"Invalid data for {symbol}: {e}")
    return None
```

### 3.2 ❌ Using print() Instead of Logger

**Severity: HIGH**

**7 instances** of `print()` for error logging:

```python
# Bad
print(f"Email error: {e}")
print(f"Telegram error: {e}")
print(f"IPO scrape error: {e}")

# Good
logger.error(f"Email error: {e}")
```

**Files affected:**
- `services/notification_service.py`
- `tasks/smart_signals.py`
- `tasks/ipo_tracker.py`
- `tasks/portfolio_advisor.py`
- `api/ipo.py`

### 3.3 ⚠️ Missing Error Context

**Severity: MEDIUM**

Exceptions raised without sufficient context:

```python
# Bad
raise HTTPException(status_code=400, detail="Invalid ID")

# Good
raise HTTPException(status_code=400, detail=f"Invalid holding ID format: {holding_id}")
```

---

## 4. Security Issues

### 4.1 ⚠️ Weak Password Hashing

**Severity: HIGH**

Using SHA256 for password hashing:

```python
# core/security.py
def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
```

**Recommendation:** Use bcrypt or argon2:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)
```

### 4.2 ⚠️ CORS Allow All Origins

**Severity: MEDIUM**

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any origin
    ...
)
```

**Recommendation:** Restrict to known origins in production:
```python
allow_origins=["https://stockpilot.example.com", "http://localhost:3000"]
```

### 4.3 ✅ JWT Implementation - OK

Token implementation is acceptable:
- Uses `python-jose` library
- Configurable expiration
- Includes user email in payload

### 4.4 ⚠️ No Input Sanitization for External APIs

**Severity: MEDIUM**

User input passed directly to external API URLs:

```python
# services/price_service.py
resp = await client.get(f"{YAHOO_CHART_URL}/{ticker}")
```

**Recommendation:** Validate and sanitize symbol input.

---

## 5. Design Pattern Issues

### 5.1 ❌ No Repository Pattern

**Severity: MEDIUM**

Direct database access in route handlers:

```python
# Bad - Direct Beanie calls in routes
@router.get("/")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    alerts = await Alert.find(Alert.user_id == PydanticObjectId(current_user["_id"])).to_list()
```

**Recommendation:** Implement repository pattern:
```python
# repositories/alert_repository.py
class AlertRepository:
    async def get_by_user(self, user_id: str) -> List[Alert]:
        return await Alert.find(Alert.user_id == PydanticObjectId(user_id)).to_list()

# routes
@router.get("/")
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    repo: AlertRepository = Depends()
):
    return await repo.get_by_user(current_user["_id"])
```

### 5.2 ❌ No Service Layer Separation

**Severity: HIGH**

Business logic mixed with HTTP handling:

```python
# api/portfolio.py - 300+ lines of business logic in route file
```

**Recommendation:** 
- Routes: HTTP request/response handling only
- Services: Business logic
- Repositories: Data access

### 5.3 ⚠️ Global State for Caching

**Severity: MEDIUM**

```python
# services/price_service.py
_cache: Dict[str, tuple] = {}  # Global mutable state
_last_request_time = 0
_rate_lock = asyncio.Lock()
```

**Recommendation:** Use Redis or proper caching library:
```python
from aiocache import Cache
cache = Cache(Cache.REDIS)
```

### 5.4 ⚠️ Missing Dependency Injection

**Severity: MEDIUM**

Services instantiated directly instead of injected:

```python
# Bad
from ..services.price_service import get_bulk_prices

# Good - Dependency injection
def get_price_service() -> PriceService:
    return PriceService()

@router.get("/")
async def get_holdings(price_service: PriceService = Depends(get_price_service)):
    ...
```

---

## 6. Code Quality Issues

### 6.1 ❌ Magic Numbers

**Severity: MEDIUM**

Hardcoded values without explanation:

```python
# api/portfolio.py
if abs(xirr_value) > 1000:  # Why 1000?

# api/goals.py
r = 0.12 / 12  # What is 0.12?

# tasks/alert_checker.py
if w52.get("high_52w") and current_price >= w52["high_52w"] * 0.98:  # Why 0.98?
```

**Recommendation:** Use named constants:
```python
# core/constants.py
XIRR_MAX_THRESHOLD = 1000
ANNUAL_RETURN_RATE = 0.12
NEAR_52W_HIGH_THRESHOLD = 0.98
```

### 6.2 ❌ Long Functions

**Severity: MEDIUM**

Functions exceeding 50 lines:

| File | Function | Lines |
|------|----------|-------|
| `api/portfolio.py` | `get_dashboard` | ~80 |
| `api/portfolio.py` | `get_portfolio_xirr` | ~50 |
| `tasks/smart_signals.py` | `analyze_stock` | ~200 |
| `tasks/portfolio_advisor.py` | `generate_recommendation` | ~150 |

**Recommendation:** Break into smaller, focused functions.

### 6.3 ⚠️ Inconsistent Response Formats

**Severity: MEDIUM**

Different response structures across endpoints:

```python
# Some return dict
return {"message": "Deleted"}

# Some return list
return [{"_id": str(a.id), ...} for a in alerts]

# Some return nested
return {"goals": result, "portfolio_value": ...}
```

**Recommendation:** Use `StandardResponse` from `core/response_handler.py`:
```python
return StandardResponse.ok(data=alerts, message="Alerts retrieved")
```

### 6.4 ⚠️ Unused Imports

**Severity: LOW**

```python
# core/exceptions.py
from typing import Optional  # Not used
```

---

## 7. Documentation Issues

### 7.1 ❌ Missing Docstrings

**Severity: HIGH**

Most functions lack docstrings:

```python
# Bad
async def get_user_holdings(user_id: str):
    return await Holding.find(...).to_list()

# Good
async def get_user_holdings(user_id: str) -> List[Holding]:
    """
    Retrieve all holdings for a user.
    
    Args:
        user_id: The user's MongoDB ObjectId as string
        
    Returns:
        List of Holding documents belonging to the user
        
    Raises:
        ValueError: If user_id is not a valid ObjectId
    """
    return await Holding.find(...).to_list()
```

### 7.2 ❌ No API Documentation

**Severity: HIGH**

FastAPI endpoints lack descriptions:

```python
# Bad
@router.get("/holdings")
async def get_holdings(...):

# Good
@router.get(
    "/holdings",
    summary="Get user holdings",
    description="Retrieve all stock holdings for the authenticated user with current prices",
    response_description="List of holdings with P&L calculations"
)
async def get_holdings(...):
```

### 7.3 ⚠️ Outdated Comments

**Severity: LOW**

```python
# services/notification_service.py
# TODO comments that should be addressed or removed
```

---

## 8. Testing Issues

### 8.1 ❌ No Unit Tests

**Severity: CRITICAL**

No test files found in the codebase.

**Recommendation:** Add tests for:
- Services (unit tests)
- API endpoints (integration tests)
- Models (validation tests)

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_price_service.py
│   │   ├── test_portfolio_service.py
│   │   └── test_auth.py
│   └── integration/
│       ├── test_portfolio_api.py
│       └── test_alerts_api.py
```

### 8.2 ❌ No Test Configuration

**Severity: HIGH**

Missing:
- `pytest.ini` or `pyproject.toml` test config
- Test database configuration
- Fixtures for common test data

---

## 9. Performance Issues

### 9.1 ⚠️ N+1 Query Pattern

**Severity: MEDIUM**

```python
# tasks/alert_checker.py
for a in alerts:
    if a.alert_type in ["WEEK_52_HIGH", ...]:
        week52_data[a.symbol] = await get_52week_data(a.symbol)  # N queries
```

**Recommendation:** Batch fetch:
```python
symbols_needing_52w = [a.symbol for a in alerts if a.alert_type in [...]]
week52_data = await get_bulk_52week_data(symbols_needing_52w)
```

### 9.2 ⚠️ No Database Indexes Defined

**Severity: MEDIUM**

Beanie models don't define indexes:

```python
# models/documents/holding.py
class Holding(BaseDocument):
    symbol: str
    # No index on user_id + symbol (frequently queried together)
```

**Recommendation:**
```python
class Holding(BaseDocument):
    symbol: str
    
    class Settings:
        name = "holdings"
        indexes = [
            [("user_id", 1), ("symbol", 1)],  # Compound index
            [("user_id", 1)],
        ]
```

---

## 10. Specific File Issues

### 10.1 `api/portfolio.py`

| Line | Issue | Severity |
|------|-------|----------|
| 11-26 | SECTOR_MAP should be in constants | Medium |
| 29-36 | Duplicate helper functions | High |
| 180-230 | XIRR logic should be in service | Medium |
| 232-300 | Dashboard function too long | Medium |

### 10.2 `services/price_service.py`

| Line | Issue | Severity |
|------|-------|----------|
| 13-14 | Global mutable state | Medium |
| 56, 93 | Bare except with logger.debug | Low |
| 70-90 | Hardcoded MoneyControl codes | Medium |

### 10.3 `tasks/smart_signals.py`

| Line | Issue | Severity |
|------|-------|----------|
| 19 | Bare except | High |
| 24-215 | analyze_stock() is 190 lines | High |
| 214 | print() instead of logger | Medium |

---

## 11. Recommendations Summary

### Critical (Must Fix)
1. Add proper exception handling - replace bare `except:` clauses
2. Replace `print()` with `logger`
3. Add unit tests
4. Use bcrypt for password hashing

### High Priority
1. Extract duplicate code to services
2. Remove duplicate service files
3. Add docstrings to all public functions
4. Implement repository pattern

### Medium Priority
1. Use constants from `core/constants.py`
2. Add type hints to all functions
3. Implement proper caching (Redis)
4. Add database indexes
5. Standardize response format

### Low Priority
1. Fix PEP8 line length violations
2. Add blank lines per PEP8
3. Remove unused imports
4. Add API documentation

---

## 12. Refactoring Checklist

- [ ] Replace all bare `except:` with specific exceptions
- [ ] Replace all `print()` with `logger.error/warning/info`
- [ ] Extract `get_user_holdings` to `services/portfolio/service.py`
- [ ] Remove duplicate service files from root
- [ ] Update all imports to use `core/security.py`
- [ ] Import `SECTOR_MAP` from `core/constants.py`
- [ ] Add type hints to all functions
- [ ] Add docstrings to all public functions
- [ ] Create `tests/` directory with pytest setup
- [ ] Add database indexes to Beanie models
- [ ] Implement bcrypt password hashing
- [ ] Restrict CORS origins for production
- [ ] Use `StandardResponse` for all endpoints

---

## Appendix: Files Reviewed

| Directory | Files | Issues Found |
|-----------|-------|--------------|
| `core/` | 8 | 3 |
| `utils/` | 4 | 1 |
| `models/` | 18 | 2 |
| `api/` | 22 | 45 |
| `services/` | 12 | 15 |
| `tasks/` | 9 | 20 |
| `middleware/` | 2 | 0 |
| **Total** | **75** | **86** |
