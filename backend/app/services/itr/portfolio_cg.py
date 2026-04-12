"""
Fetch capital gains from user's portfolio transactions.
Converts Holdings + embedded transactions to Lot/CGTransaction for FIFO engine.
"""

from datetime import date, datetime

from beanie import PydanticObjectId

from ...models.documents import Holding
from .capital_gains import CGSummary, CGTransaction, Lot, compute_capital_gains


def _parse_date(d: str | datetime) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    try:
        return datetime.fromisoformat(d).date()
    except (ValueError, TypeError):
        return date.min  # fallback for malformed dates


def _fy_range(fy: str) -> tuple[date, date]:
    """Parse FY string like '2025-26' to (start_date, end_date)."""
    try:
        start_year = int(fy.split("-")[0])
        return date(start_year, 4, 1), date(start_year + 1, 3, 31)
    except (ValueError, IndexError):
        # Default to current FY if parsing fails
        from datetime import datetime as dt

        now = dt.now()
        start_year = now.year if now.month >= 4 else now.year - 1
        return date(start_year, 4, 1), date(start_year + 1, 3, 31)


def _asset_type(holding_type: str) -> str:
    """Map holding_type to capital gains asset_type."""
    if holding_type == "MF":
        return "equity_mf"
    if holding_type == "ETF":
        return "etf_equity"
    return "equity"


async def get_portfolio_capital_gains(user_id: str, fy: str) -> CGSummary:
    """
    Compute capital gains from user's sell transactions in given FY.
    Uses FIFO matching against buy lots.
    """
    fy_start, fy_end = _fy_range(fy)
    holdings = await Holding.find(Holding.user_id == PydanticObjectId(user_id)).to_list()

    lots: list[Lot] = []
    sells: list[CGTransaction] = []

    for h in holdings:
        asset = _asset_type(h.holding_type)

        for t in h.transactions:
            t_date = _parse_date(t.date)

            if t.type == "BUY":
                lots.append(
                    Lot(
                        symbol=h.symbol,
                        buy_date=t_date,
                        quantity=t.quantity,
                        cost_per_unit=t.price,
                        asset_type=asset,
                    )
                )
            elif t.type == "SELL" and fy_start <= t_date <= fy_end:
                sells.append(
                    CGTransaction(
                        symbol=h.symbol,
                        sell_date=t_date,
                        quantity=t.quantity,
                        sale_price_per_unit=t.price,
                        asset_type=asset,
                    )
                )

    return compute_capital_gains(lots, sells)
