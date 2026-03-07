# StockPilot

Personal Portfolio Intelligence Platform — Track, analyze, and optimize your stock & mutual fund investments with real-time data, AI insights, and smart notifications.

## 🚀 Features

### Portfolio Management
- **Real-time Portfolio Tracking** — Live portfolio value with P&L, day change, XIRR
- **Holdings Management** — Stocks + Mutual Funds with dynamic All/Stocks/MF filter
- **Transaction History** — Full buy/sell history with cost basis calculation
- **Groww Import** — Import transaction history from Groww XLSX exports (stocks + MF)
- **Sector Allocation** — Visual sector breakdown with filter support
- **XIRR Calculation** — Annualized returns (separate for stocks, MF, overall)
- **Export** — Download holdings, transactions, dividends, tax reports as CSV

### Tax Center
- **Tax Summary** — STCG (20%) and LTCG (12.5% above ₹1.25L) breakdown
- **Tax Harvesting** — Top losses to harvest + gains to book, with tax saved/due
- **Advance Tax Schedule** — Quarterly advance tax calculation
- **Dividend Tax** — Dividend income for tax filing
- **Tax Report Export** — Excel export for CA/filing

### Analytics & Intelligence
- **Portfolio Metrics** — Beta, volatility, HHI, concentration risk, risk profile
- **Returns Analysis** — CAGR, holding period, benchmark comparison vs Nifty 50
- **Drawdown Analysis** — Current drawdown, recovery needed, holdings in loss
- **Sector Risk** — Concentration risk with MF categorization
- **Rebalance Suggestions** — Current vs target allocation with deviation alerts
- **MF Overlap Analyzer** — Find overlapping stocks across mutual funds
- **MF Health Check** — Fund performance vs benchmarks, expense ratio analysis
- **PnL Calendar** — Daily buy/sell activity calendar
- **Stock Comparison** — Side-by-side fundamentals comparison

### AI Chat (Groq)
- **Portfolio Assistant** — AI-powered chat with full portfolio context
- **Tax Awareness** — Knows STCG/LTCG status per holding
- **Streaming Responses** — Real-time streaming with markdown rendering
- **Dynamic Follow-ups** — Context-aware suggestion chips

### Smart Signals & Alerts
- **Trading Signals** — AI-powered buy/sell/hold recommendations with fundamentals
- **Price Alerts** — Target price, % change, 52-week high/low, volume spike
- **Notifications** — Email + Telegram + Web Push for all alert types
- **Portfolio Advisor** — Twice-daily smart analysis (9:30 AM, 3 PM)

### Market Data
- **Live Indices** — NIFTY 50, SENSEX, BANK NIFTY
- **Stock Research** — Company analysis with Screener fundamentals
- **IPO Tracking** — Upcoming IPOs with GMP, lot size, action recommendations
- **FII/DII Activity** — Foreign & domestic institutional investor flows
- **Screener** — Top gainers/losers, 52-week highs/lows, custom screens
- **Corporate Actions** — Dividends and splits for portfolio stocks

### Financial Planning
- **Goals Tracker** — Set and track financial goals with projections
- **SIP Management** — Track SIP investments with AMFI NAV integration
- **Networth Tracker** — Total networth with monthly history and YTD growth
- **8 Calculators** — Asset Allocation, SIP Step-up, Portfolio Score, Retirement, SWP, Loan Analyzer, Salary & Tax, Cashflow Planner

### Family Vault
- **Secure Storage** — Bank accounts, insurance, investments, property, legal docs
- **Nominee Access** — Share vault with family via email invite
- **File Uploads** — Attach PDF/JPG/PNG/DOC to vault entries

### Notifications
- **Hourly Updates** — Portfolio snapshot every hour (9 AM - 4 PM) via Email + Telegram
- **Daily Digest** — Portfolio summary at 6 PM via Email + Telegram
- **Price Alerts** — Instant notification when conditions are met
- **IPO Alerts** — Notify when IPOs open for subscription

### Other
- **Watchlist** — Track stocks with live prices
- **Ledger** — Track loans/debts with settlement history
- **Dark/Light Theme** — System-aware theme with manual toggle
- **Google OAuth** — One-click login with Google

## 🏗️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.10+, Uvicorn |
| Database | MongoDB Atlas (Motor + Beanie ODM) |
| Cache | Redis (Upstash) — market-aware TTL |
| AI | Groq (Llama 3.3 70B) — streaming chat |
| Market Data | Yahoo Finance API (yfinance, httpx) |
| Fundamentals | Screener.in scraping |
| Charts | Recharts, Lightweight Charts |
| Auth | JWT + Google OAuth |
| Notifications | Telegram Bot API, SMTP Email, Web Push |
| Scheduling | APScheduler (IST timezone) |
| Bot | python-telegram-bot |
| Code Quality | black, isort, ruff, pre-commit hooks |

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (Atlas or local)
- Redis (Upstash or local)
- Telegram Bot Token (optional)
- Groq API Key (optional, for AI chat)

## 🛠️ Setup

### 1. Clone & Configure

```bash
git clone <repository-url>
cd stockpilot
cp .env.example .env
# Edit .env with your credentials
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Telegram Bot (Optional)

```bash
cd bot
pip install -r requirements.txt
python main.py
```

## 🔑 Environment Variables

```env
# MongoDB
MONGODB_URI=mongodb+srv://...
MONGODB_DB=stockpilot

# Auth
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis
REDIS_URL=rediss://...
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...

# Google OAuth
GOOGLE_CLIENT_ID=...

# Telegram
TELEGRAM_BOT_TOKEN=...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...

# AI
GROQ_API_KEY=...
GEMINI_API_KEY=...
```

## 📚 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/login` | Login (JWT) |
| POST | `/api/auth/google` | Google OAuth |
| GET | `/api/auth/me` | Current user |

### Portfolio
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portfolio` | Portfolio summary |
| GET | `/api/portfolio/holdings` | All holdings with live prices |
| POST | `/api/portfolio/holdings` | Add holding |
| GET | `/api/portfolio/sectors` | Sector allocation |
| GET | `/api/portfolio/dashboard` | Dashboard (cached) |
| GET | `/api/portfolio/transactions` | Transaction history |
| POST | `/api/portfolio/transactions` | Add transaction |
| POST | `/api/portfolio/import-transactions` | Import Groww XLSX |
| GET | `/api/portfolio/mf/health` | MF health check |
| GET | `/api/portfolio/mf/overlap` | MF overlap |
| GET | `/api/portfolio/mf/expense-impact` | Expense ratio impact |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics` | Sector breakdown |
| GET | `/api/analytics/metrics` | Portfolio metrics (beta, volatility) |
| GET | `/api/analytics/returns` | Returns with CAGR |
| GET | `/api/analytics/drawdown` | Drawdown analysis |
| GET | `/api/analytics/sector-risk` | Sector concentration risk |
| GET | `/api/analytics/mf-overlap` | MF overlap analyzer |
| GET | `/api/analytics/rebalance` | Rebalance suggestions |
| GET | `/api/analytics/rebalance/allocation` | Current vs target allocation |
| GET | `/api/analytics/pnl-calendar` | PnL calendar |
| POST | `/api/analytics/signals` | Trading signals |
| GET | `/api/analytics/export/csv` | Export CSV |

### Finance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/finance/tax` | Tax summary (STCG/LTCG) |
| GET | `/api/finance/tax/harvest` | Tax harvesting |
| GET | `/api/finance/tax/advance` | Advance tax schedule |
| GET | `/api/finance/tax/export` | Tax report Excel |
| GET | `/api/finance/dividends` | Dividend income |
| GET | `/api/finance/networth` | Networth breakdown |
| GET | `/api/finance/networth/history` | Monthly networth history |
| POST | `/api/finance/networth/snapshot` | Take snapshot |
| GET | `/api/finance/goals` | Financial goals |
| GET | `/api/finance/sip` | SIP investments |
| GET | `/api/finance/sip/calculator` | SIP calculator |

### Market
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/market/indices` | NIFTY, SENSEX, BANKNIFTY |
| GET | `/api/market/quote/{symbol}` | Stock quote |
| GET | `/api/market/search` | Search stocks |
| GET | `/api/market/research/{symbol}` | Stock research |
| GET | `/api/market/compare` | Compare stocks |
| GET | `/api/market/market-summary` | Top movers |
| GET | `/api/market/fii-dii` | FII/DII data |
| GET | `/api/market/screener/gainers` | Top gainers/losers |
| GET | `/api/market/corporate-actions` | Dividends & splits |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/ask` | AI chat (streaming) |
| GET | `/api/ipo/upcoming` | Upcoming IPOs |
| GET | `/api/ipo/gmp` | IPO GMP tracker |
| GET | `/api/watchlist` | Watchlist with prices |
| GET | `/api/alerts` | Price alerts |
| GET | `/api/calculators/*` | 8 financial calculators |
| GET | `/api/vault/entries` | Vault entries |
| GET | `/api/ledger` | Ledger entries |
| GET | `/api/export/*` | CSV exports |

## ⚡ Redis Caching

All heavy endpoints are cached with market-aware TTL:

| Endpoint | TTL (Market Open) | TTL (Closed) |
|----------|-------------------|--------------|
| Dashboard, Holdings, Analytics, Metrics, Returns | 2 min | 1 hr |
| Indices, Market Summary, Watchlist | 60s | 1 hr |
| Tax, Dividends, Networth, Sectors, Drawdown, Sector Risk | 5 min | 1 hr |
| MF Health, MF Overlap, Networth History | 10 min | 10 min |
| FII/DII | 30 min | 30 min |
| IPO | 1 hr | 1 hr |

## 🤖 Background Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Price Update | Every 5 min | Update cached prices for holdings |
| Alert Check | Every 1 min | Check price alerts, send notifications |
| Hourly Update | 9 AM - 4 PM hourly | Portfolio snapshot (Email + Telegram) |
| Portfolio Advisor | 9:30 AM, 3:00 PM | Smart trading signals |
| Daily Digest | 6:00 PM | Portfolio summary (Email + Telegram) |
| Earnings Check | 9:00 AM | Upcoming earnings reminders |
| IPO Scrape | Every 2 hours | Fetch IPO data from web |
| IPO Alerts | 9:30 AM | Notify IPO openings |

## 📁 Project Structure

```
stockpilot/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app, lifespan, CORS
│   │   ├── api/v1/                    # API routes (modular)
│   │   │   ├── auth/                  # JWT + Google OAuth
│   │   │   ├── portfolio/             # Holdings, transactions, import, MF
│   │   │   ├── analytics/             # Metrics, returns, drawdown, signals
│   │   │   ├── finance/               # Tax, dividends, networth, goals, SIP
│   │   │   ├── market/                # Quotes, indices, research, screener
│   │   │   ├── chat/                  # AI chat (Groq streaming)
│   │   │   ├── calculators/           # 8 financial calculators
│   │   │   ├── vault/                 # Family vault with nominees
│   │   │   ├── ledger/                # Loan/debt tracking
│   │   │   ├── alerts/                # Price alerts
│   │   │   ├── watchlist/             # Watchlist
│   │   │   ├── ipo/                   # IPO tracking
│   │   │   └── export/                # CSV exports
│   │   ├── services/
│   │   │   ├── cache.py               # Redis cache + market_open/market_ttl
│   │   │   ├── market/                # Price service, multi-source pricing
│   │   │   ├── signals/               # AI signal engine
│   │   │   ├── notification/          # Email + Telegram + Web Push
│   │   │   ├── analytics/             # Screener fundamentals
│   │   │   ├── portfolio/             # Holdings helpers
│   │   │   └── ledger/                # Ledger service
│   │   ├── tasks/                     # APScheduler background jobs
│   │   ├── models/documents/          # Beanie ODM models
│   │   ├── core/                      # Config, security, constants
│   │   ├── middleware/                # Rate limiting
│   │   └── utils/                     # Logger, helpers
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                       # 28 Next.js pages
│       │   ├── page.js                # Dashboard
│       │   ├── portfolio/             # Holdings + import
│       │   ├── analytics/             # Charts + metrics
│       │   ├── tax/                   # Tax center
│       │   ├── chat/                  # AI chat
│       │   ├── signals/               # Trading signals
│       │   ├── calculators/           # 8 calculator components
│       │   ├── vault/                 # Family vault + shared
│       │   ├── networth/              # Networth tracker
│       │   ├── mf-health/             # MF health check
│       │   ├── mf-overlap/            # MF overlap analyzer
│       │   └── ...                    # market, ipo, watchlist, etc.
│       ├── components/                # Navbar, ChatWidget, PublicLayout
│       └── lib/                       # API client, WebSocket hook
├── bot/                               # Telegram bot
└── scripts/                           # Setup, seed data, indexes
```

## 🐛 Troubleshooting

- **Backend won't start**: Check `.env`, MongoDB URI, Python 3.10+
- **Redis errors**: Verify `REDIS_URL`, check Upstash dashboard
- **Prices not updating**: Yahoo Finance rate limits — multi-source fallback handles this
- **Alerts not sending**: Ensure `telegram_chat_id` is set and `settings.hourly_alerts`/`daily_digest` are enabled
- **Frontend build errors**: Delete `node_modules` + `.next`, run `npm install`

## 📄 License

MIT License
