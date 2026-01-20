# 📊 StockPilot - Personal Portfolio Intelligence Platform

## Product Vision

A self-hosted portfolio management and research automation platform for retail investors to track, monitor, research, and make better investment decisions.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Solution Overview](#2-solution-overview)
3. [Core Features](#3-core-features)
4. [Technical Architecture](#4-technical-architecture)
5. [Tech Stack](#5-tech-stack)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [Development Roadmap](#8-development-roadmap)
9. [Project Structure](#9-project-structure)
10. [Getting Started](#10-getting-started)

---

## 1. Problem Statement

| Pain Point | Impact |
|------------|--------|
| Manually checking stock prices daily | Wastes 15+ min/day |
| Missing important company news | Delayed reactions, losses |
| No unified view of all holdings | Confusion, poor tracking |
| Not knowing when to buy/sell | Emotional decisions |
| Missing IPO opportunities | Lost potential gains |
| Time-consuming research | 30+ min/day on research |

---

## 2. Solution Overview

**StockPilot** automates portfolio tracking and research:

- **Track**: All holdings in one dashboard
- **Monitor**: Auto price updates + smart alerts
- **Research**: Daily curated news & analysis
- **Decide**: Data-driven insights (not advice)
- **Act**: Timely alerts for opportunities

### Target User
- Retail investors with 5-50 stock holdings
- Self-directed investors who want automation
- Users who lack time for daily research

---

## 3. Core Features

### 3.1 Portfolio Tracker
- [x] Add/edit/delete holdings
- [x] Real-time price updates
- [x] Live P&L calculation
- [x] Transaction history
- [x] Portfolio allocation view
- [x] Benchmark comparison (Nifty 50)

### 3.2 Smart Alerts
- [x] Price movement alerts (±3%, ±5%, ±10%)
- [x] Target price alerts
- [x] Stop-loss alerts
- [x] 52-week high/low alerts
- [x] Volume spike alerts
- [x] News alerts
- [x] Earnings date reminders

### 3.3 Research Automation
- [x] Daily market summary
- [x] Stock news aggregation
- [x] Analyst ratings tracker
- [x] FII/DII activity monitor
- [x] Insider trading alerts
- [x] Peer comparison

### 3.4 IPO Intelligence
- [x] Upcoming IPO calendar
- [x] Live GMP tracking
- [x] Subscription status
- [x] IPO analysis summary
- [x] Allotment alerts
- [x] Listing day alerts

### 3.5 Technical Analysis
- [x] Moving averages (SMA 20, 50, 200)
- [x] RSI indicator
- [x] Support/Resistance levels
- [x] Trend detection
- [x] Basic chart patterns

### 3.6 Notifications
- [x] Telegram bot
- [x] Email daily digest
- [x] Web push notifications

---

## 4. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       STOCKPILOT                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLIENTS                                                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐              │
│  │ Web App   │  │ Telegram  │  │ Email     │              │
│  │ (Next.js) │  │ Bot       │  │ Digest    │              │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘              │
│        └──────────────┼──────────────┘                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              FastAPI Backend                         │   │
│  │  /api/portfolio  /api/alerts  /api/research         │   │
│  └─────────────────────────────────────────────────────┘   │
│                       │                                     │
│        ┌──────────────┼──────────────┐                     │
│        ▼              ▼              ▼                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Price    │  │ News     │  │ Alert    │                 │
│  │ Service  │  │ Service  │  │ Engine   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│        │              │              │                     │
│        └──────────────┼──────────────┘                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PostgreSQL    │    Redis Cache    │    Celery      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  EXTERNAL DATA SOURCES                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │Yahoo Fin│ │NSE India│ │News API │ │IPO Sites│         │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Backend | Python + FastAPI | Fast, async, easy |
| Database | **MongoDB** | Flexible schema, JSON-native |
| Cache | Redis (optional) | Fast alerts, sessions |
| Task Queue | APScheduler | Lightweight scheduling |
| Frontend | Next.js (React) | Modern, fast |
| Bot | python-telegram-bot | Easy integration |
| Email | SendGrid / SMTP | Reliable delivery |
| Hosting | AWS / Railway | Scalable |

### Python Libraries
```
fastapi          # API framework
uvicorn          # ASGI server
motor            # Async MongoDB driver
pymongo          # MongoDB driver
yfinance         # Stock data
pandas           # Data analysis
python-telegram-bot  # Telegram
httpx            # HTTP client
beautifulsoup4   # Web scraping
pydantic         # Validation
apscheduler      # Task scheduling
python-jose      # JWT tokens
passlib          # Password hashing
```

---

## 6. Database Schema (MongoDB Collections)

### users
```javascript
{
  _id: ObjectId,
  email: "user@example.com",
  password_hash: "hashed_password",
  telegram_chat_id: "123456789",
  settings: {
    alerts_enabled: true,
    daily_digest: true,
    digest_time: "18:00"
  },
  created_at: ISODate("2026-01-16T00:00:00Z"),
  updated_at: ISODate("2026-01-16T00:00:00Z")
}
```

### holdings
```javascript
{
  _id: ObjectId,
  user_id: ObjectId("ref_to_user"),
  symbol: "HDFCBANK",
  name: "HDFC Bank Ltd",
  exchange: "NSE",
  holding_type: "EQUITY", // EQUITY, ETF, MF
  quantity: 7,
  avg_price: 996.00,
  transactions: [
    {
      type: "BUY",
      quantity: 7,
      price: 996.00,
      date: ISODate("2025-06-15"),
      notes: "Initial purchase"
    }
  ],
  created_at: ISODate,
  updated_at: ISODate
}
```

### alerts
```javascript
{
  _id: ObjectId,
  user_id: ObjectId("ref_to_user"),
  symbol: "HDFCBANK",
  alert_type: "PRICE_ABOVE", // PRICE_ABOVE, PRICE_BELOW, PERCENT_CHANGE, VOLUME_SPIKE
  target_value: 1000.00,
  is_active: true,
  triggered_at: null,
  notification_sent: false,
  created_at: ISODate
}
```

### price_cache
```javascript
{
  _id: "HDFCBANK", // symbol as _id for fast lookup
  symbol: "HDFCBANK",
  name: "HDFC Bank Ltd",
  exchange: "NSE",
  current_price: 937.00,
  previous_close: 939.00,
  day_open: 937.50,
  day_high: 942.00,
  day_low: 929.60,
  day_change: -2.00,
  day_change_pct: -0.21,
  volume: 5020690,
  week_52_high: 1460.00,
  week_52_low: 1046.00,
  updated_at: ISODate
}
```

### ipos
```javascript
{
  _id: ObjectId,
  name: "Shadowfax Technologies",
  symbol: null,
  ipo_type: "MAINBOARD", // MAINBOARD, SME
  price_band: {
    low: 108,
    high: 124
  },
  lot_size: 120,
  issue_size_cr: 1200.00,
  dates: {
    open: ISODate("2026-01-20"),
    close: ISODate("2026-01-22"),
    allotment: ISODate("2026-01-23"),
    listing: ISODate("2026-01-27")
  },
  gmp: 16,
  gmp_percent: 12.90,
  subscription: {
    retail: 0,
    nii: 0,
    qib: 0,
    total: 0
  },
  status: "UPCOMING", // UPCOMING, OPEN, CLOSED, LISTED
  review: "Neutral",
  updated_at: ISODate
}
```

### watchlist
```javascript
{
  _id: ObjectId,
  user_id: ObjectId("ref_to_user"),
  symbol: "RELIANCE",
  added_at: ISODate,
  notes: "Watch for dip below 1400"
}
```

### daily_digest
```javascript
{
  _id: ObjectId,
  user_id: ObjectId("ref_to_user"),
  date: ISODate("2026-01-16"),
  portfolio_value: 72280,
  day_pnl: -450,
  day_pnl_pct: -0.6,
  total_pnl: -5904,
  total_pnl_pct: -7.6,
  top_gainer: { symbol: "SILVERBEES", change_pct: 1.2 },
  top_loser: { symbol: "DAMCAPITAL", change_pct: -2.8 },
  alerts_triggered: 2,
  sent_at: ISODate
}
```

---

## 7. API Endpoints

### Authentication
```
POST   /api/auth/register     # Register new user
POST   /api/auth/login        # Login, get JWT
POST   /api/auth/logout       # Logout
GET    /api/auth/me           # Current user
```

### Portfolio
```
GET    /api/portfolio              # Get portfolio summary
GET    /api/portfolio/holdings     # List all holdings
POST   /api/portfolio/holdings     # Add holding
PUT    /api/portfolio/holdings/:id # Update holding
DELETE /api/portfolio/holdings/:id # Delete holding
GET    /api/portfolio/performance  # P&L, returns
```

### Transactions
```
GET    /api/transactions           # List transactions
POST   /api/transactions           # Add transaction
DELETE /api/transactions/:id       # Delete transaction
```

### Alerts
```
GET    /api/alerts                 # List alerts
POST   /api/alerts                 # Create alert
PUT    /api/alerts/:id             # Update alert
DELETE /api/alerts/:id             # Delete alert
```

### Market Data
```
GET    /api/market/quote/:symbol   # Get stock quote
GET    /api/market/quotes          # Bulk quotes
GET    /api/market/search          # Search stocks
GET    /api/market/indices         # Nifty, Sensex
```

### Research
```
GET    /api/research/news/:symbol  # Stock news
GET    /api/research/analysis/:symbol # Technical analysis
GET    /api/research/peers/:symbol # Peer comparison
```

### IPO
```
GET    /api/ipo/upcoming           # Upcoming IPOs
GET    /api/ipo/open               # Currently open
GET    /api/ipo/gmp                # GMP tracker
GET    /api/ipo/:id                # IPO details
```

---

## 8. Development Roadmap

### Phase 1: Foundation (Week 1-2)
- [x] Project setup & structure
- [x] Database schema & migrations
- [x] FastAPI boilerplate
- [x] User authentication (JWT)
- [x] Price fetching service
- [x] Basic CRUD for holdings

**Deliverable**: Working API with auth + price data ✅

### Phase 2: Portfolio Core (Week 3-4)
- [x] Portfolio management endpoints
- [x] P&L calculation engine
- [x] Transaction logging
- [x] Telegram bot (basic commands)
- [x] Daily price update scheduler

**Deliverable**: Functional portfolio tracker ✅

### Phase 3: Alerts System (Week 5-6)
- [x] Alert engine
- [x] Price monitoring scheduler
- [x] Telegram notifications
- [x] Email notifications
- [x] Alert history

**Deliverable**: Smart alert system ✅

### Phase 4: Research & IPO (Week 7-8)
- [x] News aggregation service
- [x] IPO tracker & GMP scraper
- [x] Basic technical indicators
- [x] Daily digest generator

**Deliverable**: Research automation ✅

### Phase 5: Web Dashboard (Week 9-10)
- [x] Next.js frontend setup
- [x] Dashboard UI
- [x] Portfolio views
- [x] Charts & visualizations
- [x] Mobile responsive

**Deliverable**: Complete web application ✅

---

## 9. Project Structure

```
stockpilot/
├── PLAN.md                 # This file
├── README.md               # Setup instructions
├── docker-compose.yml      # Local development
├── .env.example            # Environment template
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app
│   │   ├── config.py       # Settings
│   │   ├── database.py     # MongoDB connection
│   │   │
│   │   ├── models/         # Pydantic models
│   │   │   ├── user.py
│   │   │   ├── holding.py
│   │   │   ├── alert.py
│   │   │   └── ipo.py
│   │   │
│   │   ├── api/            # API routes
│   │   │   ├── auth.py
│   │   │   ├── portfolio.py
│   │   │   ├── alerts.py
│   │   │   ├── market.py
│   │   │   └── ipo.py
│   │   │
│   │   ├── services/       # Business logic
│   │   │   ├── price_service.py
│   │   │   ├── alert_service.py
│   │   │   ├── news_service.py
│   │   │   └── ipo_service.py
│   │   │
│   │   └── tasks/          # Scheduled tasks
│   │       ├── scheduler.py
│   │       ├── price_updater.py
│   │       └── alert_checker.py
│   │
│   ├── tests/              # Unit tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── bot/
│   ├── __init__.py
│   ├── main.py             # Telegram bot
│   ├── handlers/           # Command handlers
│   │   ├── portfolio.py
│   │   ├── alerts.py
│   │   └── research.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js app router
│   │   ├── components/     # React components
│   │   ├── lib/            # Utilities
│   │   └── styles/         # CSS
│   ├── package.json
│   └── Dockerfile
│
└── scripts/
    ├── setup.sh            # Initial setup
    └── seed_data.py        # Sample data
```

---

## 10. Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)

### Quick Start

```bash
# Clone and setup
cd stockpilot
cp .env.example .env
# Edit .env with your credentials

# Setup Python environment
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

### Environment Variables
```env
# MongoDB (use your existing connection)
MONGODB_URI=mongodb://user:pass@host:27017/?authMechanism=SCRAM-SHA-1&tls=true&tlsCAFile=/path/to/cert.pem
MONGODB_DB=stockpilot

# JWT
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

---

## Next Steps

1. **Immediate**: Set up project structure
2. **Today**: Create database models
3. **This week**: Build core API endpoints
4. **Next week**: Telegram bot integration

---

## Notes

- This is a personal tool, not financial advice software
- All "suggestions" are data-driven observations, not recommendations
- User is responsible for their own investment decisions
- No auto-trading functionality (requires broker API + compliance)

---

*Last Updated: January 19, 2026*

---

## ✅ Implementation Complete

All features from the roadmap have been implemented as of January 20, 2026.

---

## 🤖 Smart Portfolio Advisor (Auto Alerts)

The system automatically analyzes your portfolio **twice daily** (9:30 AM & 3:00 PM) and sends actionable recommendations via Telegram & Email.

### Portfolio Actions

| Action | When Triggered |
|--------|----------------|
| **STRONG BUY** | RSI < 25 + Near 52-week low |
| **BUY MORE** | RSI < 35 (oversold) or sharp dip on high volume |
| **PARTIAL SELL** | RSI > 70 with good profit, or 50%+ gain with rally |
| **SELL** | RSI > 75 + Near 52-week high |
| **EXIT** | Deep loss (>20%) with no recovery signs |
| **WAIT** | Downtrend - wait for better entry |
| **HOLD** | Healthy trend, no action needed |

### IPO Recommendations

| Action | GMP Condition |
|--------|---------------|
| **APPLY** | GMP > 15% (good listing expected) |
| **RISKY** | GMP 5-15% (apply if fundamentals strong) |
| **AVOID** | GMP ≤ 0% (listing loss risk) |

### Sample Alert (Telegram)
```
🤖 StockPilot Daily Advisory
20 Jan 2026, 09:30 AM

📊 PORTFOLIO ACTIONS

🟢 BUY MORE: HDFCBANK
   CMP: ₹925.55 | Avg: ₹996.11
   📉 P&L: -7.1% | RSI: 17
   • RSI oversold (17)
   • Average down opportunity
   🎯 Target: ₹980

⏳ WAIT: RELIANCE
   CMP: ₹1406.50 | Avg: ₹1493.50
   📉 P&L: -5.8% | RSI: 17
   • Downtrend - below SMA20 & SMA50
   • Wait for RSI < 30 to add

📋 IPO RECOMMENDATIONS

✅ APPLY: Shadowfax Technologies
   Price: ₹108-124 | GMP: ₹16 (13%)
   • Good GMP - listing gain expected

⚠️ Not financial advice. Do your own research.
```

### API Endpoints
- `GET /api/research/signals/{symbol}` - Get signals for any stock
- `POST /api/research/advisor/run` - Manually trigger advisor
