import re
from datetime import datetime, timezone
from typing import Optional


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_currency(amount: float, symbol: str = "₹") -> str:
    if amount >= 10000000:
        return f"{symbol}{amount/10000000:.2f}Cr"
    if amount >= 100000:
        return f"{symbol}{amount/100000:.2f}L"
    return f"{symbol}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    return f"{value:+.{decimals}f}%"


def clean_symbol(symbol: str) -> str:
    """Remove .NS/.BO suffix from symbol"""
    return re.sub(r"\.(NS|BO)$", "", symbol.upper())


def add_ns_suffix(symbol: str) -> str:
    """Add .NS suffix if not present"""
    symbol = symbol.upper()
    if not symbol.endswith((".NS", ".BO")):
        return f"{symbol}.NS"
    return symbol


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator else default


def calculate_cagr(start_value: float, end_value: float, years: float) -> Optional[float]:
    if start_value <= 0 or years <= 0:
        return None
    return ((end_value / start_value) ** (1 / years) - 1) * 100
