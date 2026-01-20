# StockPilot

Personal Portfolio Intelligence Platform

## Architecture

See [Architecture.md](./Architecture.md) for detailed system design.

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env with your MongoDB URI

# Run server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Telegram Bot (Optional)

```bash
cd bot
pip install -r requirements.txt
python main.py
```

## API Documentation

Once running: http://localhost:8000/docs

## Features

- Portfolio tracking with real-time prices
- Smart price alerts
- IPO tracking
- Stock research & analysis
- Watchlist management
- Dividend tracking
- Portfolio export (CSV/PDF)
- Telegram bot notifications
- Daily digest & smart signals
