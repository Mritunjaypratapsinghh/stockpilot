"""Daily portfolio snapshot — saves portfolio value for growth chart."""

from datetime import datetime, timezone

from ..models.documents import Holding, PortfolioSnapshot, User
from ..services.cache import get_redis
from ..services.market.price_service import get_bulk_prices
from ..utils.logger import logger


async def take_daily_snapshot():
    redis = await get_redis()
    if redis:
        acquired = await redis.set("lock:daily_snapshot", "1", ex=120, nx=True)
        if not acquired:
            return

    users = await User.find().to_list()
    today = datetime.now(timezone.utc).date().isoformat()

    for user in users:
        try:
            # Skip if already snapped today
            existing = await PortfolioSnapshot.find_one(
                PortfolioSnapshot.user_id == user.id,
                PortfolioSnapshot.date >= datetime.fromisoformat(today),
            )
            if existing:
                continue

            holdings = await Holding.find(Holding.user_id == user.id).to_list()
            if not holdings:
                continue

            symbols = [h.symbol for h in holdings]
            prices = await get_bulk_prices(symbols)

            invested = sum(h.quantity * h.avg_price for h in holdings)
            current = sum(h.quantity * (prices.get(h.symbol, {}).get("current_price") or h.avg_price) for h in holdings)
            pnl = current - invested
            pnl_pct = (pnl / invested * 100) if invested else 0

            await PortfolioSnapshot(
                user_id=user.id,
                date=datetime.now(timezone.utc),
                value=round(current, 0),
                invested=round(invested, 0),
                pnl=round(pnl, 0),
                pnl_pct=round(pnl_pct, 2),
            ).insert()
        except Exception as e:
            logger.error(f"Snapshot failed for {user.email}: {e}")

    logger.info("Daily portfolio snapshots completed")
