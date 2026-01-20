# StockPilot Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                     │
├─────────────────────────────────┬────────────────────────────────────────────┤
│         Next.js Frontend        │           Telegram Bot                     │
│    (React 19 + Tailwind CSS)    │      (python-telegram-bot)                 │
│         localhost:3000          │                                            │
└────────────────┬────────────────┴──────────────────┬─────────────────────────┘
                 │ REST API                          │ MongoDB Direct
                 ▼                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                        │
│                     FastAPI + Uvicorn (localhost:8000)                        │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌───────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Auth   │ │ Portfolio │ │ Alerts │ │ Market │ │ Research │ │    IPO    │  │
│  └─────────┘ └───────────┘ └────────┘ └────────┘ └──────────┘ └───────────┘  │
│  ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐           │
│  │ Watchlist │ │ Dividends │ │  Export  │ │   Import  │ │ Notify │           │
│  └───────────┘ └───────────┘ └──────────┘ └───────────┘ └────────┘           │
└──────────────────────────────────────────────────────────────────────────────┘
                 │                                   │
                 ▼                                   ▼
┌────────────────────────────────┐  ┌──────────────────────────────────────────┐
│        SERVICE LAYER           │  │           BACKGROUND JOBS                 │
├────────────────────────────────┤  │          (APScheduler)                    │
│  ┌──────────────────────────┐  │  ├──────────────────────────────────────────┤
│  │     Price Service        │  │  │  • Price Updater (5 min)                 │
│  │  (Yahoo Finance API)     │  │  │  • Alert Checker (1 min)                 │
│  │  - Rate limiting         │  │  │  • Portfolio Advisor (9:30 AM, 3 PM)     │
│  │  - Caching (1min/1hr)    │  │  │  • Daily Digest (6 PM)                   │
│  └──────────────────────────┘  │  │  • Earnings Checker (9 AM)               │
│  ┌──────────────────────────┐  │  │  • IPO Scraper (2 hours)                 │
│  │  Notification Service    │  │  └──────────────────────────────────────────┘
│  │  - Telegram              │  │
│  │  - Email (SMTP)          │  │
│  │  - Web Push              │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                         │
│                         MongoDB (Motor async)                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│  Collections: users | holdings | alerts | watchlist | notifications | ipos   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Authentication Flow

```
┌────────┐      POST /api/auth/login       ┌─────────┐      find user      ┌─────────┐
│ Client │ ──────────────────────────────▶ │ FastAPI │ ──────────────────▶ │ MongoDB │
└────────┘                                 └─────────┘                     └─────────┘
    ▲                                           │
    │         { access_token: "jwt..." }        │ verify password
    └───────────────────────────────────────────┘ create JWT token
```

### 2. Portfolio Data Flow

```
┌────────┐  GET /api/portfolio/dashboard  ┌─────────┐  get holdings  ┌─────────┐
│ Client │ ─────────────────────────────▶ │ FastAPI │ ─────────────▶ │ MongoDB │
└────────┘                                └─────────┘                └─────────┘
    ▲                                          │
    │                                          ▼
    │                                   ┌─────────────┐
    │                                   │Price Service│
    │                                   └──────┬──────┘
    │                                          │ fetch live prices
    │                                          ▼
    │                                   ┌─────────────┐
    │    { holdings, sectors, xirr }   │Yahoo Finance│
    └──────────────────────────────────└─────────────┘
```

### 3. Alert Notification Flow

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
                              └───────────┬─────────────┘
                                          │ if triggered
                                          ▼
                              ┌─────────────────────────┐
                              │  Notification Service   │
                              └───────────┬─────────────┘
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              ┌──────────┐         ┌───────────┐         ┌──────────┐
              │ Telegram │         │   Email   │         │ Web Push │
              └──────────┘         └───────────┘         └──────────┘
```

### 4. Price Service Caching

```
┌─────────────────────────────────────────────────────────────────┐
│                      Price Service                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Request ──▶ Check Cache ──▶ Cache Hit? ──▶ Return cached data │
│                    │                                             │
│                    ▼ Cache Miss                                  │
│              Rate Limiter (10 req/sec)                          │
│                    │                                             │
│                    ▼                                             │
│              Yahoo Finance API                                   │
│                    │                                             │
│                    ▼                                             │
│              Store in Cache                                      │
│              TTL: 1 min (market open) / 1 hr (market closed)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
stockpilot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan, middleware
│   │   ├── database.py          # MongoDB connection (Motor)
│   │   ├── config.py            # Pydantic settings
│   │   ├── logger.py            # Logging config
│   │   ├── api/                 # REST endpoints
│   │   │   ├── auth.py          # JWT auth, login/register
│   │   │   ├── portfolio.py     # Holdings CRUD, sectors, XIRR
│   │   │   ├── alerts.py        # Price alert management
│   │   │   ├── market.py        # Live quotes, indices
│   │   │   ├── research.py      # Stock analysis, news
│   │   │   ├── ipo.py           # IPO tracking
│   │   │   ├── watchlist.py     # Watchlist management
│   │   │   ├── dividends.py     # Dividend tracking
│   │   │   ├── export.py        # CSV/PDF export
│   │   │   ├── import_holdings.py
│   │   │   └── notifications.py
│   │   ├── services/
│   │   │   ├── price_service.py      # Yahoo Finance with cache
│   │   │   └── notification_service.py
│   │   ├── tasks/               # Background jobs
│   │   │   ├── scheduler.py     # APScheduler setup
│   │   │   ├── price_updater.py
│   │   │   ├── alert_checker.py
│   │   │   ├── smart_signals.py
│   │   │   ├── portfolio_advisor.py
│   │   │   ├── digest_generator.py
│   │   │   ├── earnings_checker.py
│   │   │   └── ipo_tracker.py
│   │   ├── models/              # Pydantic schemas
│   │   └── middleware/
│   │       └── rate_limit.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   │   ├── page.js          # Dashboard
│   │   │   ├── portfolio/
│   │   │   ├── alerts/
│   │   │   ├── watchlist/
│   │   │   ├── research/
│   │   │   ├── ipo/
│   │   │   └── signals/
│   │   ├── components/
│   │   │   └── Navbar.js
│   │   └── lib/
│   │       └── api.js           # API client
│   └── package.json
├── bot/
│   ├── main.py                  # Telegram bot
│   └── requirements.txt
└── scripts/
    └── seed_data.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/portfolio` | Portfolio summary |
| GET | `/api/portfolio/holdings` | All holdings with live prices |
| POST | `/api/portfolio/holdings` | Add holding |
| PUT | `/api/portfolio/holdings/{id}` | Update holding |
| DELETE | `/api/portfolio/holdings/{id}` | Delete holding |
| GET | `/api/portfolio/sectors` | Sector allocation |
| GET | `/api/portfolio/xirr` | Annualized returns |
| GET | `/api/portfolio/dashboard` | Combined data (single call) |
| POST | `/api/portfolio/import` | Import from CSV |
| GET | `/api/alerts` | List alerts |
| POST | `/api/alerts` | Create alert |
| DELETE | `/api/alerts/{id}` | Delete alert |
| GET | `/api/market/indices` | NIFTY, SENSEX |
| GET | `/api/market/quote/{symbol}` | Stock quote |
| GET | `/api/research/analysis/{symbol}` | Technical analysis |
| GET | `/api/research/news/{symbol}` | Stock news |
| GET | `/api/ipo` | Upcoming IPOs |
| GET | `/api/watchlist` | Watchlist |
| POST | `/api/watchlist` | Add to watchlist |
| GET | `/api/dividends` | Dividend history |
| GET | `/api/export/{type}/csv` | Export data |

## Database Schema

### users
```json
{
  "_id": "ObjectId",
  "email": "string",
  "password_hash": "string",
  "telegram_chat_id": "string (optional)",
  "settings": { "alerts_enabled": true, "daily_digest": true },
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
  "quantity": 10,
  "avg_price": 2500.00,
  "transactions": [{ "type": "BUY", "quantity": 10, "price": 2500, "date": "2024-01-15" }],
  "created_at": "datetime"
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
  "triggered_at": "datetime (optional)",
  "created_at": "datetime"
}
```

## Background Jobs Schedule

| Job | Schedule | Function |
|-----|----------|----------|
| Price Update | Every 5 min | Update cached prices for all holdings |
| Alert Check | Every 1 min | Check price alerts, send notifications |
| Portfolio Advisor | 9:30 AM, 3:00 PM | Generate smart signals |
| Daily Digest | 6:00 PM | Send portfolio summary |
| Earnings Check | 9:00 AM | Remind upcoming earnings |
| IPO Scrape | Every 2 hours | Fetch upcoming IPO data |
| IPO Alerts | 9:30 AM | Notify IPO openings |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4 |
| Charts | Recharts, Lightweight Charts |
| Backend | FastAPI, Python 3.10, Uvicorn |
| Database | MongoDB (Motor async driver) |
| Auth | JWT (python-jose), SHA256 password hash |
| Market Data | Yahoo Finance API (yfinance, httpx) |
| Scheduling | APScheduler |
| Notifications | Telegram API, SMTP |
| Bot | python-telegram-bot |
