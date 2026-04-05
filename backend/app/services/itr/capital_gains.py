"""
Capital Gains Engine — FIFO lot-wise computation with grandfathering.

Handles: listed equity, equity MF, debt MF (pre/post Apr-2023), ETF, bonus, splits.
Grandfathering ceiling rule: if FMV > sale_price → cost = sale_price (no artificial loss).
LTCG 112A exemption ₹1.25L applied to AGGREGATE, not per-stock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .tax_rules import TaxRules, get_rules


@dataclass
class Lot:
    symbol: str
    isin: str = ""
    buy_date: date = date.min
    quantity: float = 0
    cost_per_unit: float = 0
    asset_type: str = "equity"  # equity / equity_mf / debt_mf / unlisted / etf_equity / etf_debt
    fmv_31jan2018: Optional[float] = None  # for grandfathering


@dataclass
class CGTransaction:
    symbol: str
    isin: str = ""
    sell_date: date = date.min
    quantity: float = 0
    sale_price_per_unit: float = 0
    asset_type: str = "equity"


@dataclass
class LotResult:
    symbol: str
    isin: str = ""
    buy_date: date = date.min
    sell_date: date = date.min
    quantity: float = 0
    cost_of_acquisition: float = 0
    sale_consideration: float = 0
    fmv_31jan2018: float = 0
    holding_months: int = 0
    is_long_term: bool = False
    gain: float = 0
    classification: str = ""  # STCG_111A / STCG_other / LTCG_112A / LTCG_other / slab_rate
    grandfathering_applied: bool = False


@dataclass
class Schedule112AEntry:
    isin: str = ""
    scrip_name: str = ""
    quantity: float = 0
    sale_price: float = 0
    sale_consideration: float = 0
    cost_of_acquisition: float = 0
    fmv_31jan2018: float = 0
    transfer_expenses: float = 0
    deductions_54f: float = 0
    ltcg: float = 0


@dataclass
class CGSummary:
    stcg_111a: int = 0
    stcg_other: int = 0
    ltcg_112a_gross: int = 0  # before exemption
    ltcg_112a_net: int = 0  # after ₹1.25L exemption
    ltcg_other: int = 0
    slab_rate_gains: int = 0  # debt MF post-2023
    lot_results: list[LotResult] = field(default_factory=list)
    schedule_112a: list[Schedule112AEntry] = field(default_factory=list)
    total_stcl: int = 0
    total_ltcl: int = 0


def _months_between(d1: date, d2: date) -> int:
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def _is_debt_mf_post_2023(asset_type: str, buy_date: date, rules: TaxRules) -> bool:
    return asset_type in ("debt_mf", "etf_debt") and buy_date >= rules.debt_mf_no_ltcg_cutoff


def _get_holding_period_months(asset_type: str, rules: TaxRules) -> int:
    if asset_type in ("equity", "equity_mf", "etf_equity"):
        return rules.holding_period_listed_equity
    if asset_type in ("debt_mf", "etf_debt"):
        return rules.holding_period_debt_mf
    if asset_type == "unlisted":
        return rules.holding_period_unlisted
    return rules.holding_period_listed_equity


def _classify(
    asset_type: str,
    is_long_term: bool,
    buy_date: date,
    rules: TaxRules,
) -> str:
    # Debt MF post-Apr-2023: always slab rate
    if _is_debt_mf_post_2023(asset_type, buy_date, rules):
        return "slab_rate"

    if asset_type in ("equity", "equity_mf", "etf_equity"):
        return "LTCG_112A" if is_long_term else "STCG_111A"

    if asset_type in ("debt_mf", "etf_debt"):
        return "LTCG_other" if is_long_term else "STCG_other"

    if asset_type == "unlisted":
        return "LTCG_other" if is_long_term else "STCG_other"

    return "STCG_other"


def _apply_grandfathering(
    actual_cost: float,
    fmv: Optional[float],
    sale_price: float,
    buy_date: date,
    rules: TaxRules,
) -> tuple[float, bool]:
    """
    Apply grandfathering for pre-31-Jan-2018 equity.
    Returns (adjusted_cost, was_grandfathering_applied).
    Ceiling rule: if FMV > sale_price → cost = sale_price.
    """
    if buy_date >= rules.grandfathering_date or fmv is None:
        return actual_cost, False

    if fmv > sale_price:
        # Ceiling rule: no artificial loss
        return sale_price, True

    return max(actual_cost, fmv), True


def compute_capital_gains(
    lots: list[Lot],
    sells: list[CGTransaction],
    rules: TaxRules | None = None,
) -> CGSummary:
    """
    FIFO lot-wise capital gains computation.
    Returns classified gains with Schedule 112A data.
    """
    rules = rules or get_rules()
    summary = CGSummary()

    # Build mutable lot pool per symbol, sorted by buy_date (FIFO)
    pool: dict[str, list[dict]] = {}
    for lot in sorted(lots, key=lambda x: x.buy_date):
        pool.setdefault(lot.symbol, []).append(
            {
                "lot": lot,
                "remaining": lot.quantity,
            }
        )

    # Process sells in chronological order
    for sell in sorted(sells, key=lambda s: s.sell_date):
        remaining_to_sell = sell.quantity
        symbol_pool = pool.get(sell.symbol, [])

        for pool_entry in symbol_pool:
            if remaining_to_sell <= 0:
                break
            if pool_entry["remaining"] <= 0:
                continue

            lot: Lot = pool_entry["lot"]
            qty = min(remaining_to_sell, pool_entry["remaining"])
            pool_entry["remaining"] -= qty
            remaining_to_sell -= qty

            sale_consideration = qty * sell.sale_price_per_unit
            actual_cost = qty * lot.cost_per_unit

            # Grandfathering
            fmv_total = qty * lot.fmv_31jan2018 if lot.fmv_31jan2018 else None
            cost, gf_applied = _apply_grandfathering(
                actual_cost,
                fmv_total,
                sale_consideration,
                lot.buy_date,
                rules,
            )

            holding = _months_between(lot.buy_date, sell.sell_date)
            threshold = _get_holding_period_months(lot.asset_type, rules)
            is_lt = holding > threshold
            classification = _classify(lot.asset_type, is_lt, lot.buy_date, rules)
            gain = sale_consideration - cost

            lr = LotResult(
                symbol=sell.symbol,
                isin=sell.isin or lot.isin,
                buy_date=lot.buy_date,
                sell_date=sell.sell_date,
                quantity=qty,
                cost_of_acquisition=cost,
                sale_consideration=sale_consideration,
                fmv_31jan2018=fmv_total or 0,
                holding_months=holding,
                is_long_term=is_lt,
                gain=gain,
                classification=classification,
                grandfathering_applied=gf_applied,
            )
            summary.lot_results.append(lr)

            # Aggregate
            g = int(gain)
            if classification == "STCG_111A":
                summary.stcg_111a += g
            elif classification == "STCG_other":
                summary.stcg_other += g
            elif classification == "LTCG_112A":
                summary.ltcg_112a_gross += g
                # Schedule 112A entry
                summary.schedule_112a.append(
                    Schedule112AEntry(
                        isin=lr.isin,
                        scrip_name=sell.symbol,
                        quantity=qty,
                        sale_price=sell.sale_price_per_unit,
                        sale_consideration=sale_consideration,
                        cost_of_acquisition=cost,
                        fmv_31jan2018=lr.fmv_31jan2018,
                        ltcg=g,
                    )
                )
            elif classification == "LTCG_other":
                summary.ltcg_other += g
            elif classification == "slab_rate":
                summary.slab_rate_gains += g

    # Apply LTCG 112A exemption (aggregate)
    if summary.ltcg_112a_gross > 0:
        summary.ltcg_112a_net = max(0, summary.ltcg_112a_gross - rules.ltcg_112a_exemption)
    else:
        summary.ltcg_112a_net = summary.ltcg_112a_gross  # loss, no exemption

    # Track losses
    if summary.stcg_111a < 0:
        summary.total_stcl += abs(summary.stcg_111a)
    if summary.stcg_other < 0:
        summary.total_stcl += abs(summary.stcg_other)
    if summary.ltcg_112a_gross < 0:
        summary.total_ltcl += abs(summary.ltcg_112a_gross)
    if summary.ltcg_other < 0:
        summary.total_ltcl += abs(summary.ltcg_other)

    return summary
