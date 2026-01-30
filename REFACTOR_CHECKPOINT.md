# Backend Refactoring Checkpoint

## Last Updated: 2026-01-31 02:00 IST
## Branch: refactor-backend
## Latest Commit: ce29e520

---

## Phase 3: Code Review Findings (PENDING FIXES)

### 🔴 CRITICAL (5 issues)

1. **Duplicate auth functions** - `api/v1/auth/routes.py` L20-37
   - `create_access_token` and `get_current_user` duplicated from `core/security.py`
   - FIX: Remove duplicates, import from core/security

2. **Alert type mismatch** - `models/documents/alert.py` L10
   - Model: `Literal["PRICE_ABOVE", "PRICE_BELOW"]`
   - Used in code: PERCENT_CHANGE, WEEK_52_HIGH, WEEK_52_LOW, VOLUME_SPIKE, EARNINGS
   - FIX: Update Literal to include all 9 types

3. **AlertCreate schema mismatch** - `api/v1/alerts/schemas.py` L10
   - Only allows 2 types, should match model
   - FIX: Sync with updated Alert model

4. **sys.path hack** - `services/analytics/service.py` L135-137
   - Dangerous `sys.path.append()` inside function
   - FIX: Use proper relative imports

5. **Wrong import path** - `services/analytics/service.py` L141
   - `from ..services.market.price_service` should be `from ..market.price_service`

### 🟠 HIGH (8 issues)

6. **Bare exceptions** - 18 occurrences across 8 files
   - Files: price_service.py, multi_source_price.py, analytics/service.py, smart_signals.py, ipo_tracker.py, portfolio_advisor.py, notification/service.py, database.py
   - FIX: Use specific exception types (httpx.HTTPError, KeyError, ValueError)

7-10. **Missing return type hints** - 4 files
   - notification/service.py: send_email, send_web_push, send_alert_notification, send_daily_digest
   - portfolio_advisor.py: get_stock_data, get_bulk_stock_data, analyze_ipo_opportunities, run_portfolio_advisor, send_advisor_alert
   - smart_signals.py: analyze_stock, check_smart_signals, send_smart_alert
   - ipo_tracker.py: parse_date_range, scrape_ipo_data, check_ipo_alerts

11-13. **Memory leaks** - 3 locations
   - `middleware/rate_limit.py` L7: RateLimiter.requests grows unbounded
   - `services/market/price_service.py` L14: _cache no max size
   - `tasks/portfolio_advisor.py` L14: _advisor_cache no max size
   - FIX: Add TTL cleanup or max size limits

### 🟡 MEDIUM (9 issues)

14-16. **TODO comments in production** - 3 files
   - services/alerts/__init__.py, services/finance/__init__.py, services/auth/__init__.py

17. **Enum case mismatch** - `api/v1/finance/schemas.py` L17
   - Schema: `Literal["MONTHLY", "WEEKLY"]`
   - Model: `Literal["monthly", "weekly", "quarterly"]`

18-19. **Goal field name mismatch**
   - Model has `current_value`, routes use `current_amount`

20-21. **Dividend sorting error** - `api/v1/finance/routes.py` L73
   - Sorts by `Dividend.date` but model has `ex_date`

22. **Incomplete core/schemas.py** - Missing re-exports

### 🟢 LOW (9 issues)

23-25. **Duplicate route decorators** - portfolio, alerts, watchlist routes
26-27. **Commented imports** - transaction.py, price_cache.py
28. **Unused IST variable** - scheduler.py
29. **Wrong env_file path** - core/config.py
30. **Redundant added_at field** - watchlist.py
31. **Mixed Beanie/Motor** - notification/service.py

### 🔵 ARCHITECTURAL (5 issues)

32. Duplicate service files at root and subdirectories
33. Inconsistent import patterns (3 vs 4 dots)
34. No shared ID validator
35. Hardcoded User-Agent in 10+ places
36. Scattered timeout values instead of using constants

---

## Completed Phases

### Phase 1 ✅ (Commit: 5765c8a)
- Created core/ module (config, database, security, constants, exceptions, response_handler, schemas)
- Created utils/ module (logger, enums, helpers)
- Restructured models/ (documents/ + schemas.py)
- Migrated all 8 tasks to Beanie ODM

### Phase 2 ✅ (Commit: ce29e520)
- Created api/v1/auth/ with routes.py and schemas.py
- Organized v1 modules to aggregate routes
- Moved services to subdirectories (market/, notification/, analytics/)
- Updated main.py with legacy route compatibility

---

## Next Steps (Phase 3)

1. Fix all 5 critical issues
2. Fix 8 high priority issues  
3. Address medium/low as time permits
4. Run full test suite
5. Commit Phase 3 fixes
