# StockPilot

## Tech Stack
- **Language**: Python 3.10+ (backend), JavaScript/React 19 (frontend)
- **Framework**: FastAPI + Uvicorn (backend), Next.js 16 (frontend)
- **Database**: MongoDB Atlas (Motor async + Beanie ODM)
- **Cache**: Redis (Upstash) — market-aware TTL via `market_open()` / `market_ttl()`
- **AI**: Groq (Llama 3.3 70B) for streaming chat, custom SignalEngine for trading signals
- **Notifications**: Telegram Bot API + SMTP Email + Web Push
- **Market Data**: Yahoo Finance API (httpx), Screener.in (BeautifulSoup)
- **Charts**: Recharts, Lightweight Charts
- **Auth**: JWT (python-jose) + Google OAuth
- **Scheduling**: APScheduler (IST timezone)
- **Code Quality**: black, isort, ruff, pre-commit hooks

## Architecture Overview
Personal Portfolio Intelligence Platform with:
- 13 API modules (auth, portfolio, analytics, finance, market, chat, calculators, vault, ledger, alerts, watchlist, ipo, export)
- 17+ Redis-cached endpoints with market-aware TTL
- 9 background jobs (price updates, alerts, hourly/daily notifications, IPO scraping, signals)
- AI chat with full portfolio context (STCG/LTCG, holding periods, XIRR)
- Multi-channel notifications (Email + Telegram + Web Push)

## Key Files
- **Entry point**: `backend/app/main.py`
- **Config**: `backend/app/core/config.py`, `.env`
- **Database**: `backend/app/core/database.py` (Motor + Beanie init)
- **Cache**: `backend/app/services/cache.py` (Redis + market helpers)
- **Routes**: `backend/app/api/v1/*/routes.py` (13 modules)
- **Models**: `backend/app/models/documents/*.py` (18 Beanie documents)
- **Tasks**: `backend/app/tasks/scheduler.py` (APScheduler setup)
- **Frontend API**: `frontend/src/lib/api.js`
- **Frontend pages**: `frontend/src/app/*/page.js` (28+ pages)

## Data Flow
1. Frontend → FastAPI REST API → Redis cache check → MongoDB + Yahoo Finance → cache result → response
2. APScheduler → background tasks → price updates / alert checks → notification service → Email + Telegram
3. AI Chat → build portfolio context (holdings + STCG/LTCG + periods) → Groq streaming → SSE response

## External Dependencies
- Yahoo Finance API (market data, charts, corporate actions)
- Screener.in (company fundamentals scraping)
- MongoDB Atlas (persistent storage)
- Upstash Redis (response caching)
- Groq API (AI chat - Llama 3.3 70B)
- Telegram Bot API (notifications + bot commands)
- Google OAuth (authentication)
- AMFI (mutual fund NAV data)

## Environment Variables
```
MONGODB_URI, MONGODB_DB
SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
REDIS_URL, UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN
GOOGLE_CLIENT_ID
TELEGRAM_BOT_TOKEN
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
GROQ_API_KEY, GEMINI_API_KEY
```

## Common Commands
- **Backend**: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
- **Frontend**: `cd frontend && npm run dev`
- **Bot**: `cd bot && python main.py`
- **Lint**: `cd backend && black . && isort . && ruff check .`
- **Pre-commit**: `pre-commit run --all-files`
