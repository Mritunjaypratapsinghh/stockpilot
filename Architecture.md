# StockPilot Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                     │
├─────────────────────────────────┬────────────────────────────────────────────┤
│         Next.js Frontend        │           Telegram Bot                     │
│    (React 19 + Tailwind CSS 4)  │      (python-telegram-bot)                 │
│         localhost:3000          │                                            │
└────────────────┬────────────────┴──────────────────┬─────────────────────────┘
                 │ REST API                          │ MongoDB Direct
                 ▼                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                        │
│                     FastAPI + Uvicorn (localhost:8000)                        │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ │
│  │  Auth   │ │ Portfolio │ │Analytics │ │Finance │ │  Market  │ │  Chat  │ │
│  └─────────┘ └───────────┘ └──────────┘ └────────┘ └──────────┘ └────────┘ │
│  ┌─────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ │
│  │ Alerts  │ │ Watchlist │ │  Vault   │ │ Ledger │ │   IPO    │ │ Export │ │
│  └─────────┘ └───────────┘ └──────────┘ └────────┘ └──────────┘ └────────┘ │
│  ┌──────────────┐                                                            │
│  │ Calculators  │  (8 financial calculators)                                 │
│  └──────────────┘                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
                 │                                   │
                 ▼                                   ▼
┌────────────────────────────────┐  ┌──────────────────────────────────────────┐
│        SERVICE LAYER           │  │           BACKGROUND JOBS                 │
├────────────────────────────────┤  │          (APScheduler IST)               │
│  ┌──────────────────────────┐  │  ├──────────────────────────────────────────┤
│  │     Price Service        │  │  │  • Price Updater (5 min)                 │
│  │  (Multi-source Yahoo)    │  │  │  • Alert Checker (1 min)                 │
│  │  - Market-aware cache    │  │  │  • Hourly Update (9-4 PM, Email+TG)     │
│  │  - 60s/1hr TTL           │  │  │  • Portfolio Advisor (9:30 AM, 3 PM)     │
│  └──────────────────────────┘  │  │  • Daily Digest (6 PM, Email+TG)        │
│  ┌──────────────────────────┐  │  │  • Earnings Checker (9 AM)               │
│  │     Redis Cache          │  │  │  • IPO Scraper (2 hours)                 │
│  │  (Upstash)               │  │  │  • IPO Alerts (9:30 AM)                  │
│  │  - market_open() helper  │  │  │  • WS Broadcaster (5 sec)                │
│  │  - market_ttl() helper   │  │  └──────────────────────────────────────────┘
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  Notification Service    │  │
│  │  - Telegram Bot API      │  │
│  │  - Email (SMTP)          │  │
│  │  - Web Push              │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  AI Services             │  │
│  │  - Groq (Llama 3.3 70B) │  │
│  │  - Signal Engine         │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  Analytics Service       │  │
│  │  - Screener.in scraping  │  │
│  │  - Fundamentals data     │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                         │
│              MongoDB Atlas (Motor async + Beanie ODM)                         │
├──────────────────────────────────────────────────────────────────────────────┤
│  users | holdings | alerts | watchlist | notifications | ipos | price_cache  │
│  goals | sips | assets | ledger_entries | networth_history | daily_digests   │
│  vault_entries | vault_nominees | advisor_history | signal_history           │
│  dividends | portfolio_snapshots                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Authentication Flow

```
┌────────┐   POST /api/auth/login    ┌─────────┐   find user    ┌─────────┐
│ Client │ ────────────────────────▶ │ FastAPI │ ──────────────▶│ MongoDB │
└────────┘                           └─────────┘                └─────────┘
    ▲                                     │
    │    { access_token: "jwt..." }       │ verify password / Google OAuth
    └─────────────────────────────────────┘ create JWT token
```

### 2. Portfolio Dashboard Flow (with Redis Cache)

```
┌────────┐  GET /api/portfolio/dashboard  ┌─────────┐  check cache  ┌───────┐
│ Client │ ─────────────────────────────▶ │ FastAPI │ ────────────▶ │ Redis │
└────────┘                                └─────────┘               └───────┘
    ▲                                          │                       │
    │                                          │ cache miss            │ cache hit
    │                                          ▼                       │ (30ms)
    │                                   ┌─────────────┐                │
    │                                   │   MongoDB   │                │
    │                                   │ (holdings)  │                │
    │                                   └──────┬──────┘                │
    │                                          ▼                       │
    │                                   ┌─────────────┐                │
    │                                   │Price Service│                │
    │                                   │(Yahoo + MF) │                │
    │                                   └──────┬──────┘                │
    │                                          │                       │
    │                                          ▼                       │
    │                                   ┌─────────────┐                │
    │    { holdings, xirr, sectors }    │ Cache result│                │
    │◀──────────────────────────────────│ TTL: 2m/1hr │◀───────────────┘
    │                                   └─────────────┘
```

### 3. AI Chat Flow

```
┌────────┐  POST /api/chat/ask     ┌─────────┐  build context  ┌─────────┐
│ Client │ ──────────────────────▶ │ FastAPI │ ──────────────▶ │ MongoDB │
└────────┘                         └─────────┘                 └─────────┘
    ▲                                   │                          │
    │ SSE stream                        │ holdings + STCG/LTCG     │
    │ (real-time)                       │ + holding periods        │
    │                                   ▼                          │
    │                            ┌─────────────┐                   │
    │◀───────────────────────────│    Groq     │                   │
    │  streaming tokens          │ Llama 3.3   │                   │
    │                            │  70B, 800t  │                   │
    │                            └─────────────┘
```

### 4. Alert Notification Flow

```
┌───────────────┐                    ┌─────────────┐
│ APScheduler   │ ─── every 1 min ─▶│Alert Checker│
│ (Background)  │                    └──────┬──────┘
└───────────────┘                           │
                                            ▼
                              ┌─────────────────────────┐
                              │ 1. Fetch active alerts  │
                              │ 2. Get bulk prices      │
                              │ 3. Check conditions     │
                              │ 4. Get 52-week data     │
                              └───────────┬─────────────┘
                                          │ if triggered
                                          ▼
                              ┌─────────────────────────┐
                              │  Notification Service   │
                              │  (ObjectId user lookup) │
                              └───────────┬─────────────┘
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              ┌──────────┐         ┌───────────┐         ┌──────────┐
              │ Telegram │         │   Email   │         │ Web Push │
              └──────────┘         └───────────┘         └──────────┘
```

### 5. Redis Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Market-Aware Cache                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   market_open() → Mon-Fri 9:15 AM - 3:30 PM IST                │
│                                                                  │
│   Request ──▶ cache_get(key) ──▶ Hit? ──▶ Return (30ms)        │
│                    │                                             │
│                    ▼ Miss                                        │
│              Compute result (2-14s)                              │
│                    │                                             │
│                    ▼                                             │
│              cache_set(key, result, ttl=market_ttl())           │
│                                                                  │
│   TTL Strategy:                                                  │
│   ┌──────────────────┬──────────────┬──────────────┐            │
│   │ Endpoint Type    │ Market Open  │ Market Close │            │
│   ├──────────────────┼──────────────┼──────────────┤            │
│   │ Price-dependent  │ 60s - 2min   │ 1 hour       │            │
│   │ Analysis         │ 5 min        │ 1 hour       │            │
│   │ Heavy compute    │ 10 min       │ 10 min       │            │
│   │ External scrape  │ 30min - 1hr  │ 30min - 1hr  │            │
│   └──────────────────┴──────────────┴──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 6. Groww XLSX Import Flow

```
┌────────┐  POST /import-transactions  ┌─────────┐
│ Client │ ──────── XLSX file ───────▶ │ FastAPI │
└────────┘                             └────┬────┘
                                            │
                              ┌─────────────▼─────────────┐
                              │ Auto-detect format:       │
                              │ "Symbol" → Stocks         │
                              │ "Scheme Name" → MF        │
                              └─────────┬─────────────────┘
                    ┌───────────────────┼───────────────────┐
                    ▼                                       ▼
          ┌─────────────────┐                    ┌─────────────────┐
          │ Stock Import    │                    │ MF Import       │
          │ Counter dedup   │                    │ Replace all txns│
          │ Append new txns │                    │ (source of truth│
          │ Recalc avg_price│                    │ MF_SYMBOL_MAP)  │
          └─────────────────┘                    └─────────────────┘
```

## Project Structure

```
stockpilot/
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI app, lifespan, CORS, scheduler
│   │   ├── api/v1/                        # Versioned API routes
│   │   │   ├── __init__.py                # Router aggregation (13 modules)
│   │   │   ├── auth/routes.py             # JWT + Google OAuth
│   │   │   ├── portfolio/routes.py        # Holdings, transactions, import, MF, XIRR
│   │   │   ├── analytics/routes.py        # Metrics, returns, drawdown, signals, overlap
│   │   │   ├── finance/routes.py          # Tax, dividends, networth, goals, SIP
│   │   │   ├── market/routes.py           # Quotes, indices, research, screener, FII/DII
│   │   │   ├── chat/routes.py             # Groq AI streaming chat
│   │   │   ├── calculators/routes.py      # 8 financial calculators
│   │   │   ├── vault/routes.py            # Family vault + nominees + file uploads
│   │   │   ├── ledger/routes.py           # Loan/debt tracking + settlements
│   │   │   ├── alerts/routes.py           # Price alerts CRUD
│   │   │   ├── watchlist/routes.py        # Watchlist with live prices
│   │   │   ├── ipo/routes.py              # IPO tracking + GMP
│   │   │   └── export/routes.py           # CSV exports
│   │   ├── services/
│   │   │   ├── cache.py                   # Redis: cache_get/set, market_open, market_ttl
│   │   │   ├── websocket.py               # WebSocket manager
│   │   │   ├── market/
│   │   │   │   ├── price_service.py       # Yahoo Finance with rate limiting
│   │   │   │   └── multi_source_price.py  # Multi-source fallback + market-aware cache
│   │   │   ├── signals/engine.py          # AI signal engine (fundamentals + technicals)
│   │   │   ├── notification/service.py    # Email + Telegram + Web Push
│   │   │   ├── analytics/service.py       # Screener.in fundamentals scraping
│   │   │   ├── portfolio/service.py       # get_user_holdings, get_prices_for_holdings
│   │   │   └── ledger/service.py          # Ledger business logic
│   │   ├── tasks/
│   │   │   ├── scheduler.py               # APScheduler setup (IST timezone)
│   │   │   ├── price_updater.py           # Update PriceCache every 5 min
│   │   │   ├── alert_checker.py           # Check price alerts every 1 min
│   │   │   ├── hourly_update.py           # Portfolio snapshot (Email + Telegram)
│   │   │   ├── portfolio_advisor.py       # Smart signals + IPO recommendations
│   │   │   ├── digest_generator.py        # Daily digest at 6 PM
│   │   │   ├── earnings_checker.py        # Earnings reminders
│   │   │   ├── ipo_tracker.py             # Scrape IPO data + alerts
│   │   │   ├── smart_signals.py           # Legacy signal system
│   │   │   └── ws_broadcaster.py          # WebSocket price broadcast
│   │   ├── models/documents/              # Beanie ODM models
│   │   │   ├── base.py                    # BaseDocument (user_id, timestamps)
│   │   │   ├── user.py                    # User + settings + push subscription
│   │   │   ├── holding.py                 # Holdings + embedded transactions
│   │   │   ├── alert.py                   # Price alerts (6 types)
│   │   │   ├── watchlist.py               # Watchlist items
│   │   │   ├── vault.py                   # Vault entries + nominees
│   │   │   ├── ledger.py                  # Ledger entries + settlements
│   │   │   ├── goal.py                    # Financial goals
│   │   │   ├── sip.py                     # SIP investments
│   │   │   ├── asset.py                   # Other assets (for networth)
│   │   │   ├── ipo.py                     # IPO data
│   │   │   ├── price_cache.py             # Cached stock prices
│   │   │   ├── networth_history.py        # Monthly networth snapshots
│   │   │   ├── daily_digest.py            # Digest history
│   │   │   ├── advisor_history.py         # Advisor run history
│   │   │   ├── signal_history.py          # Signal history
│   │   │   ├── dividend.py                # Dividend records
│   │   │   ├── notification.py            # In-app notifications
│   │   │   └── portfolio_snapshot.py      # Portfolio snapshots
│   │   ├── core/
│   │   │   ├── config.py                  # Pydantic settings (env vars)
│   │   │   ├── database.py                # MongoDB init (Motor + Beanie)
│   │   │   ├── security.py                # JWT + password hashing
│   │   │   ├── constants.py               # SECTOR_MAP, MF categories
│   │   │   ├── response_handler.py        # StandardResponse wrapper
│   │   │   └── exceptions.py              # Custom exceptions
│   │   ├── middleware/rate_limit.py        # Rate limiting
│   │   └── utils/
│   │       ├── logger.py                  # Logging config
│   │       ├── helpers.py                 # Utility functions
│   │       └── enums.py                   # AlertType, AlertStatus
│   ├── requirements.txt
│   ├── pyproject.toml                     # black, isort, ruff config
│   └── pytest.ini
├── frontend/
│   └── src/
│       ├── app/                           # 28+ Next.js pages
│       │   ├── page.js                    # Dashboard
│       │   ├── layout.js                  # Root layout + ChatWidget
│       │   ├── portfolio/page.js          # Holdings + import modal
│       │   ├── analytics/page.js          # Charts + metrics
│       │   ├── tax/page.js                # Tax center (harvest + summary)
│       │   ├── chat/page.js               # AI chat (markdown + follow-ups)
│       │   ├── signals/page.js            # Trading signals
│       │   ├── calculators/               # 8 calculator components
│       │   │   ├── page.js                # Calculator hub
│       │   │   ├── AssetAllocation.js
│       │   │   ├── SIPStepup.js
│       │   │   ├── PortfolioScore.js
│       │   │   ├── RetirementPlanner.js
│       │   │   ├── SWPCalculator.js
│       │   │   ├── LoanAnalyzer.js
│       │   │   ├── SalaryTax.js
│       │   │   └── CashflowPlanner.js
│       │   ├── vault/page.js              # Family vault
│       │   ├── vault/shared/page.js       # Nominee view
│       │   ├── networth/page.js           # Networth tracker
│       │   ├── mf-health/page.js          # MF health check
│       │   ├── mf-overlap/page.js         # MF overlap analyzer
│       │   ├── market/page.js             # Market overview
│       │   ├── ipo/page.js                # IPO tracker
│       │   ├── watchlist/page.js          # Watchlist
│       │   ├── alerts/page.js             # Price alerts
│       │   ├── research/page.js           # Stock research
│       │   ├── compare/page.js            # Stock comparison
│       │   ├── screener/page.js           # Stock screener
│       │   ├── pnl/page.js                # PnL calendar
│       │   ├── rebalance/page.js          # Rebalance suggestions
│       │   ├── goals/page.js              # Financial goals
│       │   ├── sip/page.js                # SIP management
│       │   ├── ledger/page.js             # Ledger
│       │   ├── settings/page.js           # User settings
│       │   ├── login/page.js              # Login + Google OAuth
│       │   ├── landing/page.js            # Public landing page
│       │   ├── about/page.js              # About page
│       │   ├── services/page.js           # Services page
│       │   ├── corporate-actions/page.js  # Dividends & splits
│       │   └── stock/page.js              # Individual stock view
│       ├── components/
│       │   ├── Navbar.js                  # Main navigation
│       │   ├── ChatWidget.js              # Floating AI chat
│       │   ├── ChatWidgetWrapper.js       # Client wrapper
│       │   ├── PublicLayout.js            # Public page layout
│       │   └── PublicNavbar.js            # Public navigation
│       └── lib/
│           ├── api.js                     # API client (fetch wrapper)
│           └── useWebSocket.js            # WebSocket hook
├── bot/
│   ├── main.py                            # Telegram bot commands
│   ├── handlers/                          # Bot command handlers
│   └── requirements.txt
├── scripts/
│   ├── setup.sh                           # Setup script
│   ├── seed_data.py                       # Seed data
│   └── create_indexes.py                  # MongoDB indexes
├── .pre-commit-config.yaml                # black, isort, ruff hooks
├── .env.example                           # Environment template
└── .gitignore
```

## Database Schema (Beanie ODM)

### users
```json
{
  "_id": "ObjectId",
  "email": "string",
  "password_hash": "string",
  "google_id": "string (optional)",
  "telegram_chat_id": "string (optional)",
  "settings": {
    "alerts_enabled": true,
    "daily_digest": true,
    "hourly_alerts": true,
    "email_alerts": true
  },
  "push_subscription": {},
  "created_at": "datetime"
}
```

### holdings
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "symbol": "RELIANCE",
  "name": "Reliance Industries",
  "exchange": "NSE",
  "holding_type": "EQUITY | MF",
  "quantity": 10.0,
  "avg_price": 2500.00,
  "current_price": 2650.00,
  "sector": "Oil & Gas",
  "transactions": [
    { "type": "BUY", "quantity": 10, "price": 2500, "date": "2024-01-15" }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### alerts
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "symbol": "HDFCBANK",
  "alert_type": "PRICE_ABOVE | PRICE_BELOW | PERCENT_CHANGE | WEEK_52_HIGH | WEEK_52_LOW | VOLUME_SPIKE",
  "target_value": 1700.00,
  "is_active": true,
  "notification_sent": false,
  "triggered_at": "datetime (optional)"
}
```

### vault_entries
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "category": "bank | insurance | investment | property | legal | digital | contact",
  "name": "HDFC Savings",
  "details": {},
  "files": ["filename.pdf"],
  "nominees": [{ "email": "...", "accepted": true }]
}
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4 | UI |
| Backend | FastAPI, Python 3.10+, Uvicorn | API server |
| Database | MongoDB Atlas (Motor + Beanie ODM) | Persistent storage |
| Cache | Redis (Upstash) | Market-aware response caching |
| AI Chat | Groq (Llama 3.3 70B) | Portfolio assistant |
| AI Signals | Custom SignalEngine | Buy/sell/hold recommendations |
| Market Data | Yahoo Finance API (httpx) | Live prices, charts |
| Fundamentals | Screener.in (BeautifulSoup) | Company financials |
| Charts | Recharts, Lightweight Charts | Data visualization |
| Auth | JWT (python-jose) + Google OAuth | Authentication |
| Notifications | Telegram Bot API + SMTP + Web Push | Multi-channel alerts |
| Scheduling | APScheduler (IST) | Background jobs |
| Bot | python-telegram-bot | Telegram interface |
| Code Quality | black, isort, ruff, pre-commit | Formatting & linting |
| Deployment | Heroku (backend), Vercel (frontend) | Hosting |
