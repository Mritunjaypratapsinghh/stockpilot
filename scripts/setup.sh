#!/bin/bash
set -e
echo "🚀 Setting up StockPilot..."
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
[ ! -f ../.env ] && cp ../.env.example ../.env && echo "📝 Edit .env with credentials"
echo "✅ Done! Run: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
