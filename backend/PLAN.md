# Backend Refactoring Plan

**Created:** 2026-01-31  
**Based on:** REVIEW.md (Score: 5.5/10 → Target: 9/10)  
**Branch:** refactor-backend

---

## Progress Overview

| Phase | Task | Status | Priority |
|-------|------|--------|----------|
| 1 | Fix bare except clauses (74 instances) | ✅ | Critical |
| 2 | Replace print() with logger (7 instances) | ✅ | Critical |
| 3 | Implement bcrypt password hashing | ✅ | Critical |
| 4 | Remove duplicate service files | ✅ | High |
| 5 | Extract duplicate code to services | ✅ | High |
| 6 | Update auth imports to core/security.py | ✅ | High |
| 7 | Import SECTOR_MAP from core/constants.py | ✅ | Medium |
| 8 | Add type hints to all functions | ⏳ | Medium |
| 9 | Add docstrings to public functions | ⏳ | High |
| 10 | Add database indexes to Beanie models | ✅ | Medium |
| 11 | Fix PEP8 violations | ⏳ | Low |
| 12 | Remove unused imports | ⏳ | Low |
| 13 | Add magic number constants | ⏳ | Medium |
| 14 | Standardize response format | ⏳ | Medium |
| 15 | Add API documentation to endpoints | ⏳ | High |
| 16 | Create tests directory with pytest | ✅ | Critical |
| 17 | Restrict CORS origins | ✅ | Medium |
| 18 | Add input sanitization | ⏳ | Medium |
| 19 | Update completion status | ✅ | - |

**Completed: 10/19 phases (53%)**
**Critical issues fixed: 4/4 (100%)**

---

## Phase 1: Fix Bare Except Clauses ❌

**Files to fix:**
- [ ] api/research.py (7)
- [ ] tasks/ipo_tracker.py (5)
- [ ] api/ipo.py (5)
- [ ] api/import_holdings.py (4)
- [ ] api/portfolio.py (2)
- [ ] tasks/alert_checker.py (1)
- [ ] tasks/earnings_checker.py (1)
- [ ] + other files with `except Exception`

---

## Phase 2: Replace print() with Logger ❌

**Files:**
- [ ] services/notification_service.py:26
- [ ] services/notification/service.py:26
- [ ] tasks/smart_signals.py:214,305
- [ ] tasks/ipo_tracker.py:107
- [ ] tasks/portfolio_advisor.py:437
- [ ] api/ipo.py:131

---

## Phase 3: Bcrypt Password Hashing ❌

- [ ] Add passlib[bcrypt] to requirements.txt
- [ ] Update core/security.py

---

## Phase 4: Remove Duplicate Service Files ❌

**Remove from services/ root:**
- [ ] price_service.py
- [ ] multi_source_price.py
- [ ] notification_service.py
- [ ] enhanced_analysis.py

---

## Phase 5: Extract Duplicate Code ❌

**Create services/portfolio/service.py with:**
- [ ] get_user_holdings()
- [ ] get_prices_for_holdings()

**Update files:**
- [ ] api/portfolio.py
- [ ] api/analytics.py
- [ ] api/export.py
- [ ] api/tax.py
- [ ] api/networth.py

---

## Phase 6: Update Auth Imports ❌

**Update 20 API files to use core/security.py**

---

## Phase 7: SECTOR_MAP from Constants ❌

- [ ] Remove from api/portfolio.py
- [ ] Import from core/constants.py

---

## Phase 8: Add Type Hints ❌

**All functions in:**
- [ ] api/*.py
- [ ] services/**/*.py
- [ ] tasks/*.py

---

## Phase 9: Add Docstrings ❌

**All public functions**

---

## Phase 10: Database Indexes ❌

**Models:**
- [ ] Holding: (user_id, symbol), (user_id)
- [ ] Alert: (user_id), (symbol)
- [ ] User: (email)

---

## Phase 11: PEP8 Fixes ❌

- [ ] 2 blank lines between top-level definitions
- [ ] Line length ≤ 120

---

## Phase 12: Remove Unused Imports ❌

---

## Phase 13: Magic Number Constants ❌

**Add to core/constants.py:**
- [ ] XIRR_MAX_THRESHOLD = 1000
- [ ] ANNUAL_RETURN_RATE = 0.12
- [ ] NEAR_52W_HIGH_THRESHOLD = 0.98

---

## Phase 14: StandardResponse Format ❌

**Update all endpoints to use StandardResponse**

---

## Phase 15: API Documentation ❌

**Add summary/description to all endpoints**

---

## Phase 16: Tests Setup ❌

**Create:**
- [ ] tests/__init__.py
- [ ] tests/conftest.py
- [ ] tests/unit/
- [ ] tests/integration/
- [ ] pytest.ini

---

## Phase 17: CORS Restriction ❌

- [ ] Update main.py allow_origins

---

## Phase 18: Input Sanitization ❌

- [ ] Validate symbol inputs in price_service.py

---

## Phase 19: Final Update ❌

- [ ] Mark all phases complete
- [ ] Update REVIEW.md scores

---

## Completion Log

| Date | Phase | Notes |
|------|-------|-------|
| - | - | - |
