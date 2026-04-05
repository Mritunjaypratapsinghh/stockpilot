"""
Scope Checker — Detect unsupported cases and hard-block BEFORE user invests time.

Scans portfolio transactions, AIS entries, and user profile for:
- F&O / derivatives
- Intraday trading
- NRI status
- Business / professional income
- Foreign income / assets
- Crypto / VDA
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Blocker:
    blocker_type: str
    message: str
    guidance: str


@dataclass
class ScopeResult:
    supported: bool
    blockers: list[Blocker] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# F&O / derivative patterns
_FNO_PATTERNS = re.compile(
    r"(NIFTY|BANKNIFTY|FINNIFTY|MIDCPNIFTY|SENSEX)"
    r"|(\d{2}[A-Z]{3}\d{2,4}(CE|PE)$)"  # e.g. 25APR24500CE
    r"|(FUT$|FUTIDX|FUTSTK|OPTIDX|OPTSTK)",
    re.IGNORECASE,
)

_CRYPTO_PATTERNS = re.compile(
    r"(BTC|ETH|USDT|BNB|SOL|XRP|DOGE|ADA|DOT|MATIC|SHIB|AVAX)" r"[-/]?(INR|USDT|USD|BUSD)|CRYPTO|VDA|VIRTUAL.DIGITAL",
    re.IGNORECASE,
)

_BUSINESS_AIS_CODES = frozenset(
    {
        "GST_TURNOVER",
        "BUSINESS_RECEIPTS",
        "44AD",
        "44ADA",
        "44AE",
        "PROFESSIONAL_RECEIPTS",
    }
)


def check_scope(
    transactions: list[dict] | None = None,
    residency: str = "resident",
    ais_entries: list[dict] | None = None,
    has_foreign_income: bool = False,
    has_foreign_assets: bool = False,
) -> ScopeResult:
    """
    Run all scope checks. Returns ScopeResult with blockers if unsupported.

    transactions: list of dicts with keys: symbol, exchange_segment, transaction_type,
                  buy_date, sell_date, quantity
    ais_entries: list of dicts with keys: info_code, description
    """
    blockers: list[Blocker] = []
    warnings: list[str] = []
    transactions = transactions or []
    ais_entries = ais_entries or []

    # 1. NRI check
    if residency.lower() != "resident":
        blockers.append(
            Blocker(
                "NRI",
                "NRI taxation has different rules.",
                "This system supports resident Indians only. Please consult a CA.",
            )
        )

    # 2. F&O / derivatives
    for txn in transactions:
        symbol = txn.get("symbol", "")
        segment = txn.get("exchange_segment", "")
        if _FNO_PATTERNS.search(symbol) or "FNO" in segment.upper() or "DERIVATIVE" in segment.upper():
            blockers.append(
                Blocker(
                    "F&O",
                    f"F&O/derivative transaction detected: {symbol}",
                    "F&O income requires ITR-3 with business income computation. Please consult a CA.",
                )
            )
            break

    # 3. Intraday (same-day buy+sell of same symbol)
    day_trades: dict[tuple[str, date], set[str]] = {}
    for txn in transactions:
        symbol = txn.get("symbol", "")
        txn_date = txn.get("date")
        txn_type = txn.get("transaction_type", "").upper()
        if txn_date and symbol and txn_type in ("BUY", "SELL"):
            if isinstance(txn_date, str):
                txn_date = date.fromisoformat(txn_date)
            key = (symbol, txn_date)
            day_trades.setdefault(key, set()).add(txn_type)

    for (symbol, d), types in day_trades.items():
        if "BUY" in types and "SELL" in types:
            blockers.append(
                Blocker(
                    "INTRADAY",
                    f"Intraday trade detected: {symbol} on {d}",
                    "Intraday trading is speculative business income requiring ITR-3. Please consult a CA.",
                )
            )
            break

    # 4. Crypto / VDA
    for txn in transactions:
        symbol = txn.get("symbol", "")
        if _CRYPTO_PATTERNS.search(symbol):
            blockers.append(
                Blocker(
                    "CRYPTO",
                    f"Crypto/VDA transaction detected: {symbol}",
                    "Virtual Digital Asset income has special rules (30% flat tax, no set-off). Not yet supported.",
                )
            )
            break

    # 5. Business / professional income from AIS
    for entry in ais_entries:
        code = entry.get("info_code", "").upper()
        desc = entry.get("description", "").upper()
        if code in _BUSINESS_AIS_CODES or "BUSINESS" in desc or "GST" in desc:
            blockers.append(
                Blocker(
                    "BUSINESS_INCOME",
                    f"Business/professional income detected in AIS: {entry.get('description', '')}",
                    "Business income requires ITR-3/ITR-4. Please consult a CA.",
                )
            )
            break

    # 6. Foreign income / assets
    if has_foreign_income or has_foreign_assets:
        blockers.append(
            Blocker(
                "FOREIGN",
                "Foreign income or assets detected.",
                "Foreign income requires ITR-2 with Schedule FA. Currently not supported.",
            )
        )

    return ScopeResult(
        supported=len(blockers) == 0,
        blockers=blockers,
        warnings=warnings,
    )
