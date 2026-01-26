# StockPilot

Personal Portfolio Intelligence Platform - Track, analyze, and optimize your stock investments with real-time data and smart insights.

## 🚀 Features

### Portfolio Management
- **Real-time Portfolio Tracking** - Live portfolio value updates with P&L tracking
- **Transaction Management** - Record buy/sell transactions with automatic cost basis calculation
- **Mutual Fund Support** - Track MF investments with amount-based transactions and auto unit calculation
- **Holdings Analysis** - Detailed breakdown with dynamic All/Stocks/Mutual Funds filter
- **Sector Allocation** - Visual sector breakdown that updates based on selected filter
- **Import Holdings** - Bulk import from CSV/Excel files (Zerodha, Groww)
- **Export Reports** - Download portfolio reports in CSV/PDF format

### Market Intelligence
- **Live Market Data** - Real-time stock prices powered by Yahoo Finance
- **Stock Research** - Comprehensive company analysis with financials and key metrics
- **IPO Tracking** - Track upcoming and recent IPOs with subscription details
- **Market Overview** - Monitor indices and market trends

### Smart Alerts & Notifications
- **Price Alerts** - Set target price alerts for stocks
- **Smart Signals** - AI-powered buy/sell recommendations with detailed explanations
- **Telegram Integration** - Receive instant notifications on Telegram
- **Hourly Updates** - Portfolio snapshots every hour during market hours (9AM-4PM)
- **Daily Digest** - Automated daily portfolio summary at 6 PM

### Watchlist & Monitoring
- **Custom Watchlists** - Create and manage multiple watchlists
- **Dividend Tracking** - Track dividend payments and yields
- **Performance Analytics** - Historical performance charts and metrics

## 🏗️ Architecture

**Tech Stack:**
- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** Next.js 14 (React)
- **Database:** MongoDB
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Charts:** Recharts
- **Notifications:** Telegram Bot API

See [Architecture.md](./Architecture.md) for detailed system design.

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (Atlas or local instance)
- Telegram Bot Token (optional, for notifications)

## 🛠️ Installation & Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd stockpilot
```

### 2. Environment Configuration

Create `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
MONGODB_DB=stockpilot

# JWT Authentication
SECRET_KEY=your-generated-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

**Generate Secret Key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload
```

Backend will run on: http://127.0.0.1:8000

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on: http://localhost:3000

### 5. Telegram Bot (Optional)

```bash
cd bot
pip install -r requirements.txt
python main.py
```

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

### API Endpoints

**Authentication:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

**Portfolio:**
- `GET /api/portfolio` - Get portfolio summary
- `GET /api/portfolio/holdings` - List all holdings
- `POST /api/portfolio/transactions` - Add transaction
- `GET /api/portfolio/transactions` - List transactions

**Market Data:**
- `GET /api/market/search` - Search stocks
- `GET /api/market/quote/{symbol}` - Get stock quote
- `GET /api/market/chart/{symbol}` - Get price chart data

**Alerts:**
- `POST /api/alerts` - Create price alert
- `GET /api/alerts` - List user alerts
- `DELETE /api/alerts/{id}` - Delete alert

**Research:**
- `GET /api/research/{symbol}` - Get stock research data
- `GET /api/research/{symbol}/financials` - Get financial statements

**IPO:**
- `GET /api/ipo/upcoming` - List upcoming IPOs
- `GET /api/ipo/recent` - List recent IPOs

**Watchlist:**
- `POST /api/watchlist` - Add to watchlist
- `GET /api/watchlist` - Get watchlist
- `DELETE /api/watchlist/{symbol}` - Remove from watchlist

**Export:**
- `GET /api/export/portfolio/csv` - Export portfolio as CSV
- `GET /api/export/portfolio/pdf` - Export portfolio as PDF

## 🎨 Frontend Pages

- `/` - Dashboard with portfolio overview
- `/portfolio` - Detailed portfolio view
- `/market` - Market overview and stock search
- `/research` - Stock research and analysis
- `/watchlist` - Watchlist management
- `/alerts` - Price alerts management
- `/ipo` - IPO tracking
- `/signals` - Smart trading signals
- `/login` - User authentication

## 🔧 Configuration

### MongoDB Setup

1. Create a free MongoDB Atlas cluster at https://cloud.mongodb.com
2. Create a database user with read/write permissions
3. Whitelist your IP address (or use 0.0.0.0/0 for development)
4. Copy the connection string to `.env`

### Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/botfather) on Telegram
2. Copy the bot token to `.env`
3. Start the bot service
4. Send `/start` to your bot to link your account

## 🚀 Deployment

### Backend (FastAPI)

Deploy to:
- AWS Lambda + API Gateway
- Google Cloud Run
- Heroku
- DigitalOcean App Platform

### Frontend (Next.js)

Deploy to:
- Vercel (recommended)
- Netlify
- AWS Amplify
- Cloudflare Pages

## 📝 Development

### Project Structure

```
stockpilot/
├── backend/
│   ├── app/
│   │   ├── api/          # API route handlers
│   │   ├── models/       # Pydantic models
│   │   ├── services/     # Business logic
│   │   ├── tasks/        # Background tasks
│   │   ├── middleware/   # Custom middleware
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # MongoDB connection
│   │   └── main.py       # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   └── package.json
├── bot/
│   └── main.py           # Telegram bot
├── .env                  # Environment variables
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🐛 Troubleshooting

**Backend won't start:**
- Ensure `.env` file exists in project root
- Verify MongoDB connection string is correct
- Check Python version (3.10+ required)

**Frontend build errors:**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Clear Next.js cache: `rm -rf .next`

**Database connection issues:**
- Verify MongoDB Atlas IP whitelist
- Check database user permissions
- Ensure connection string includes database name

## 📞 Support

For issues and questions, please open an issue on GitHub.
