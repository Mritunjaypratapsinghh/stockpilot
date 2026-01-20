# StockPilot - Development Context

## Project Overview
Personal Portfolio Intelligence Platform for Indian retail investors. Tracks stocks, provides automated buy/sell recommendations, and sends alerts.

## Tech Stack
- **Backend**: FastAPI + MongoDB + APScheduler
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS
- **Data Source**: Yahoo Finance API (free, unofficial)
- **Notifications**: Telegram Bot + Email
- **Auth**: JWT

## Architecture

```
Frontend (Next.js) → FastAPI Backend → MongoDB
                          ↓
                    Yahoo Finance API
                          ↓
                    APScheduler (Background Tasks)
                          ↓
                    Telegram/Email Notifications
```

## Key Features Implemented

### Backend (`/backend/app/`)

| Feature | File | Description |
|---------|------|-------------|
| Auth | `api/auth.py` | JWT login/register with rate limiting (5 req/min) |
| Portfolio | `api/portfolio.py` | Holdings CRUD, dashboard endpoint, sectors, XIRR |
| Alerts | `api/alerts.py` | Price alert management |
| Market | `api/market.py` | Stock quotes, search with rate limiting |
| Research | `api/research.py` | Technical analysis, charts, news |
| IPO | `api/ipo.py` | IPO tracker with Mainboard/SME filter, lot sizes |
| Transactions | `api/transactions.py` | Buy/sell transaction history |
| Import | `api/import_holdings.py` | CSV import (Zerodha/Groww) |

### Background Tasks (`/backend/app/tasks/`)

| Task | Schedule | Purpose |
|------|----------|---------|
| `price_updater` | Every 5 min | Refresh cached prices |
| `alert_checker` | Every 1 min | Trigger user price alerts |
| `portfolio_advisor` | 9:30 AM & 3 PM | Smart buy/sell recommendations |
| `daily_digest` | 6 PM | Daily summary email |
| `earnings_checker` | 9 AM | Earnings date reminders |
| `ipo_tracker` | Every 2 hours | Update IPO listings |

### Services (`/backend/app/services/`)

| Service | Purpose |
|---------|---------|
| `price_service.py` | Yahoo Finance API with rate limiting + smart caching |
| `notification_service.py` | Telegram + Email delivery |

### Middleware (`/backend/app/middleware/`)

| Middleware | Purpose |
|------------|---------|
| `rate_limit.py` | In-memory rate limiting by IP |

### Frontend (`/frontend/src/app/`)

| Page | Features |
|------|----------|
| `/portfolio` | Dashboard with holdings, sectors chart, XIRR, transactions tab |
| `/stock?s=SYMBOL` | Stock detail with candlestick chart, technicals, news |
| `/research` | Stock analysis with autocomplete search |
| `/alerts` | Price alert management |
| `/ipo` | IPO tracker with Mainboard/SME tabs |
| `/watchlist` | Stock watchlist |
| `/market` | Market overview |
| `/signals` | Trading signals |

## Recent Implementations (This Session)

1. **Logging** - Centralized logger (`app/logger.py`) with file + console output
2. **Rate Limiting** - Auth (5/min), Search (20/min), API (60/min)
3. **Smart Caching** - 60s during market hours, 1 hour when closed
4. **Broker CSV Import** - Zerodha tradebook + Groww holdings
5. **Sector Allocation** - Portfolio breakdown by sector with visual bar
6. **XIRR Calculation** - True annualized returns from transactions
7. **Transaction Tracking** - Record Trade UI with buy/sell history
8. **Stock Autocomplete** - Search dropdown in Record Trade + Research
9. **IPO Enhancements** - Mainboard/SME filter, lot size, min investment, closed IPO filter
10. **Stock Detail Page** - Candlestick charts (lightweight-charts), technicals, news
11. **Dashboard API** - Single endpoint returning all portfolio data (4 calls → 1)
12. **Market Hours Cache** - Extended cache TTL when market is closed
13. **Dividend Tracker** - Record dividends, view by year/stock, calculate yield (`app/api/dividends.py`)
14. **Export Reports** - CSV export for holdings, transactions, dividends, full summary (`app/api/export.py`)

## Portfolio Advisor Logic

Rule-based technical analysis:

| Signal | Conditions |
|--------|------------|
| STRONG BUY | RSI < 25 AND near 52-week low |
| BUY MORE | RSI < 35 OR big drop with high volume |
| SELL | RSI > 75 AND near 52-week high |
| PARTIAL SELL | RSI > 70 with >30% profit |
| EXIT | Down >20% with no recovery signs |
| HOLD | RSI 40-60, above SMA50 |

## External APIs

| API | Purpose | Free? |
|-----|---------|-------|
| Yahoo Finance | Prices, charts, search | Yes (unofficial) |
| Telegram Bot | Push notifications | Yes |
| NSE India | FII/DII data | Yes |
| InvestorGain/IPOWatch | IPO GMP scraping | Yes |

## File Structure

```
stockpilot/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── models/        # Pydantic models
│   │   ├── services/      # Business logic
│   │   ├── tasks/         # Background jobs
│   │   ├── middleware/    # Rate limiting
│   │   ├── main.py        # FastAPI app
│   │   ├── database.py    # MongoDB connection
│   │   ├── config.py      # Settings
│   │   └── logger.py      # Logging setup
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # Shared components
│   │   └── lib/api.js     # API client
│   └── package.json
└── bot/                   # Telegram bot
```

## Environment Variables

```env
MONGODB_URI=mongodb://...
SECRET_KEY=your-jwt-secret
TELEGRAM_BOT_TOKEN=your-bot-token
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email
SMTP_PASSWORD=your-app-password
```

## Running the Project

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

## Future Improvements (Not Yet Implemented)

- Mobile responsive tables
- Form validation
- Error boundaries
- PWA support
- Multi-currency (US stocks)
- Tax reports (LTCG/STCG)
- Broker API sync (auto-import)
- Redis caching (for multi-instance)
- Unit tests

## Notes

- Yahoo Finance API is unofficial - can break if they change endpoints
- IPO lot sizes are estimated (SEBI guidelines)
- Sector mapping is hardcoded for ~80 major NSE stocks
- Rate limiter is in-memory (resets on server restart)
