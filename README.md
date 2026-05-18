# StockPilot

AI-powered personal portfolio intelligence platform for Indian investors. Track stocks & mutual funds, get trading signals, tax insights, and smart alerts.

## What It Does

- **Portfolio Tracking** — Real-time holdings with P&L, XIRR, sector allocation
- **Tax Center** — STCG/LTCG breakdown, tax harvesting, advance tax schedule
- **ITR Filing** — 12-step wizard with AIS/26AS parsing, FIFO capital gains, regime comparison
- **AI Chat** — Portfolio-aware assistant with streaming responses (Groq/Llama 3.3)
- **Smart Signals** — AI-powered buy/sell/hold recommendations
- **Alerts** — Price targets, 52-week highs/lows, volume spikes via Email + Telegram
- **MF Analytics** — Overlap analyzer, health check, expense impact
- **Financial Planning** — Goals, SIP tracker, networth history, 8 calculators
- **Family Vault** — Secure document storage with nominee access

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.10+, Uvicorn |
| Database | MongoDB Atlas (Motor + Beanie ODM) |
| Cache | Redis (Upstash) — market-aware TTL |
| AI | Groq (Llama 3.3 70B) — streaming chat |
| Market Data | Yahoo Finance (yfinance, httpx) |
| Auth | JWT (httpOnly cookies) + Google OAuth |
| Notifications | Telegram Bot, SMTP Email, Web Push |
| Scheduling | APScheduler (IST timezone) |
| CI/CD | GitHub Actions, Docker, Koyeb + Vercel |

## Quick Start

```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env  # Edit with your credentials
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Project Structure

```
stockpilot/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers (auth, portfolio, analytics, finance, itr, chat, market, vault)
│   │   ├── core/            # Config, security, database, constants
│   │   ├── middleware/      # Rate limiting, security headers
│   │   ├── models/documents/# Beanie ODM models
│   │   ├── services/        # Business logic (base, itr, market, portfolio, chat, signals)
│   │   ├── tasks/           # APScheduler background jobs
│   │   └── utils/           # Logger, pagination, helpers
│   └── tests/               # pytest (unit, edge_cases, security)
├── frontend/
│   └── src/
│       ├── app/             # Next.js pages (28 routes)
│       ├── components/      # Navbar, ChatWidget, ErrorBoundary
│       └── lib/             # API client, WebSocket hook
├── Dockerfile               # Backend (multi-stage, non-root)
├── Dockerfile.frontend      # Frontend (standalone)
├── docker-compose.yml       # Full stack (backend + redis + frontend)
└── .github/workflows/ci.yml # Lint + test + build
```

## Environment Variables

See `.env.example` for full reference. Required:

```env
SECRET_KEY=your-jwt-secret
MONGODB_URI=mongodb+srv://...
REDIS_URL=redis://...
```

## Testing

```bash
cd backend && source venv/bin/activate
python -m pytest tests/ -v  # 100 tests covering tax engine, capital gains, security
```

## Deployment

```bash
# Docker
docker-compose up --build

# Or deploy separately:
# Backend → Koyeb (auto-deploys from main)
# Frontend → Vercel (auto-deploys from main)
```

## API Overview

| Module | Endpoints | Description |
|--------|-----------|-------------|
| Auth | 5 | Register, login, Google OAuth, logout, settings |
| Portfolio | 17 | Holdings, transactions, import, sectors, dashboard |
| Analytics | 12 | Metrics, returns, drawdown, signals, rebalance |
| Finance | 15 | Tax, dividends, networth, goals, SIP |
| ITR | 18 | Profile, upload, reconcile, compute, export |
| Market | 8 | Quotes, indices, research, screener |
| Chat | 2 | AI streaming chat with portfolio context |
| Vault | 10 | Entries, nominees, file upload/download |

## License

MIT
