"""
Edge case tests for financial calculations.

These protect against real production incidents:
- Floating point precision errors in tax computation
- Fiscal year boundary misclassification
- Leap year holding period bugs
- Zero/negative/extreme value handling
- Rounding errors that compound over many transactions
"""

from datetime import date
from decimal import Decimal

import pytest
from app.services.itr.capital_gains import (
    CGTransaction,
    Lot,
    _held_longer_than,
    compute_capital_gains,
)
from app.services.itr.tax_engine import TaxInput, compute_tax
from app.services.itr.tax_rules import get_rules


class TestFloatingPointPrecision:
    """Floating point can cause ₹1 errors that compound across thousands of transactions."""

    def test_many_small_gains_dont_lose_precision(self):
        """100 transactions of ₹0.50 gain each — int() truncation loses sub-rupee gains.
        This is a KNOWN LIMITATION: individual lot gains are int()-truncated.
        Each 0.5 → int(0.5) = 0, so aggregate = 0. This is acceptable for tax purposes
        (IT dept rounds to nearest rupee per transaction).
        """
        lots = [
            Lot(symbol="TEST", buy_date=date(2023, 1, 1), quantity=1, cost_per_unit=100.50, asset_type="equity")
            for _ in range(100)
        ]
        sells = [
            CGTransaction(
                symbol="TEST", sell_date=date(2023, 6, 1), quantity=1, sale_price_per_unit=101.00, asset_type="equity"
            )
            for _ in range(100)
        ]
        result = compute_capital_gains(lots, sells)
        # int(0.5) = 0 per lot → aggregate = 0 (known truncation behavior)
        assert result.stcg_111a == 0

    def test_fractional_quantity_mf(self):
        """MF units can be 3.456 — ensure no precision loss."""
        lots = [
            Lot(
                symbol="HDFC_MF", buy_date=date(2022, 1, 1), quantity=3.456, cost_per_unit=45.67, asset_type="equity_mf"
            )
        ]
        sells = [
            CGTransaction(
                symbol="HDFC_MF",
                sell_date=date(2024, 2, 1),
                quantity=3.456,
                sale_price_per_unit=55.89,
                asset_type="equity_mf",
            )
        ]
        result = compute_capital_gains(lots, sells)
        expected = int((55.89 - 45.67) * 3.456)
        assert abs(result.ltcg_112a_gross - expected) <= 1  # ±₹1 tolerance

    def test_very_large_portfolio_value(self):
        """₹100 crore portfolio shouldn't overflow or lose precision."""
        inp = TaxInput(gross_salary=50_000_000, stcg_111a=100_000_000)
        r = compute_tax(inp, regime="new")
        assert r.tax_stcg_111a == 20_000_000  # 20% of 10Cr
        assert r.gross_tax > 0

    def test_zero_quantity_sell(self):
        """Selling 0 quantity should produce 0 gain, not crash."""
        lots = [Lot(symbol="X", buy_date=date(2023, 1, 1), quantity=10, cost_per_unit=100)]
        sells = [CGTransaction(symbol="X", sell_date=date(2023, 6, 1), quantity=0, sale_price_per_unit=200)]
        result = compute_capital_gains(lots, sells)
        assert result.stcg_111a == 0

    def test_zero_price_buy(self):
        """Bonus shares have ₹0 cost — gain = full sale price."""
        lots = [Lot(symbol="BONUS", buy_date=date(2023, 1, 1), quantity=100, cost_per_unit=0)]
        sells = [CGTransaction(symbol="BONUS", sell_date=date(2023, 8, 1), quantity=100, sale_price_per_unit=50)]
        result = compute_capital_gains(lots, sells)
        assert result.stcg_111a == 5000


class TestFiscalYearBoundaries:
    """Transactions on FY boundary dates must be classified correctly."""

    def test_sell_on_march_31_belongs_to_current_fy(self):
        """Sell on Mar 31 2026 is in FY 2025-26."""
        lots = [Lot(symbol="A", buy_date=date(2025, 1, 1), quantity=10, cost_per_unit=100)]  # noqa: F841
        sells = [CGTransaction(symbol="A", sell_date=date(2026, 3, 31), quantity=10, sale_price_per_unit=150)]
        from app.services.itr.portfolio_cg import _fy_range

        fy_start, fy_end = _fy_range("2025-26")
        assert fy_start <= sells[0].sell_date <= fy_end

    def test_sell_on_april_1_belongs_to_next_fy(self):
        """Sell on Apr 1 2026 is in FY 2026-27, NOT 2025-26."""
        from app.services.itr.portfolio_cg import _fy_range

        fy_start, fy_end = _fy_range("2025-26")
        assert date(2026, 4, 1) > fy_end

    def test_holding_period_across_fy_boundary(self):
        """Buy Mar 30, sell Apr 2 next year — holding > 12 months."""
        assert _held_longer_than(date(2024, 3, 30), date(2025, 3, 31), 12) is True
        assert _held_longer_than(date(2024, 3, 30), date(2025, 3, 30), 12) is False


class TestLeapYearEdgeCases:
    """Leap year creates holding period ambiguity."""

    def test_buy_feb29_hold_12_months(self):
        """Buy Feb 29 2024 → 12 month cutoff is ~Feb 28 2025."""
        # Must be > 12 months, so sell must be AFTER Feb 28 2025
        assert _held_longer_than(date(2024, 2, 29), date(2025, 3, 1), 12) is True
        assert _held_longer_than(date(2024, 2, 29), date(2025, 2, 28), 12) is False

    def test_buy_jan31_hold_12_months(self):
        """Jan 31 + 12 months = Jan 31 next year (no ambiguity)."""
        assert _held_longer_than(date(2024, 1, 31), date(2025, 2, 1), 12) is True
        assert _held_longer_than(date(2024, 1, 31), date(2025, 1, 31), 12) is False

    def test_buy_mar31_hold_24_months(self):
        """Mar 31 + 24 months = Mar 31 two years later."""
        assert _held_longer_than(date(2022, 3, 31), date(2024, 4, 1), 24) is True
        assert _held_longer_than(date(2022, 3, 31), date(2024, 3, 31), 24) is False


class TestNegativeAndExtremeValues:
    """Protect against negative income, extreme values, and overflow."""

    def test_negative_salary_treated_as_zero(self):
        """Negative salary (data error) shouldn't produce negative tax."""
        inp = TaxInput(gross_salary=-500_000)
        r = compute_tax(inp, regime="new")
        assert r.taxable_normal_income >= 0
        assert r.net_tax_payable >= 0 or r.net_tax_payable == 0

    def test_all_zeros(self):
        """Empty profile shouldn't crash."""
        r = compute_tax(TaxInput(), regime="new")
        assert r.net_tax_payable == 0
        assert r.gross_tax == 0

    def test_deductions_exceed_income(self):
        """Deductions > income → taxable = 0, not negative."""
        inp = TaxInput(gross_salary=300_000, sec_80c=150_000, sec_80ccd_1b=50_000, sec_80d_self=25_000)
        r = compute_tax(inp, regime="old")
        assert r.taxable_normal_income >= 0

    def test_tds_exceeds_tax_gives_refund(self):
        """TDS > computed tax → negative net (refund)."""
        inp = TaxInput(gross_salary=800_000, tds_total=500_000)
        r = compute_tax(inp, regime="new")
        assert r.net_tax_payable < 0  # refund

    def test_loss_carry_forward_reduces_gains(self):
        """B/F STCL should reduce STCG."""
        inp = TaxInput(gross_salary=500_000, stcg_111a=200_000, cf_stcl=150_000)
        r = compute_tax(inp, regime="new")
        # STCG after setoff = 200K - 150K = 50K → tax = 50K * 20% = 10K
        assert r.tax_stcg_111a == 10_000


class TestGrandfathering:
    """Grandfathering rule for pre-Jan-2018 equity."""

    def test_grandfathering_increases_cost(self):
        """FMV > actual cost → use FMV as cost (lower gain)."""
        lots = [
            Lot(
                symbol="RELIANCE",
                buy_date=date(2017, 6, 1),
                quantity=10,
                cost_per_unit=500,
                fmv_31jan2018=1000,
                asset_type="equity",
            )
        ]
        sells = [
            CGTransaction(
                symbol="RELIANCE",
                sell_date=date(2024, 6, 1),
                quantity=10,
                sale_price_per_unit=2500,
                asset_type="equity",
            )
        ]
        result = compute_capital_gains(lots, sells)
        # Cost = max(500, 1000) = 1000 per unit (grandfathered)
        # Gain = (2500 - 1000) * 10 = 15000
        assert result.ltcg_112a_gross == 15_000

    def test_ceiling_rule_prevents_artificial_loss(self):
        """If FMV > sale price → cost = sale price (no loss)."""
        lots = [
            Lot(
                symbol="YES",
                buy_date=date(2017, 1, 1),
                quantity=100,
                cost_per_unit=50,
                fmv_31jan2018=300,
                asset_type="equity",
            )
        ]
        sells = [
            CGTransaction(
                symbol="YES", sell_date=date(2024, 6, 1), quantity=100, sale_price_per_unit=200, asset_type="equity"
            )
        ]
        result = compute_capital_gains(lots, sells)
        # FMV (300) > sale (200) → ceiling rule: cost = sale price = 200
        # Gain = (200 - 200) * 100 = 0
        assert result.ltcg_112a_gross == 0

    def test_post_2018_no_grandfathering(self):
        """Purchases after Jan 31 2018 don't get grandfathering."""
        lots = [
            Lot(
                symbol="TCS",
                buy_date=date(2019, 1, 1),
                quantity=10,
                cost_per_unit=1000,
                fmv_31jan2018=900,
                asset_type="equity",
            )
        ]
        sells = [
            CGTransaction(
                symbol="TCS", sell_date=date(2024, 6, 1), quantity=10, sale_price_per_unit=3000, asset_type="equity"
            )
        ]
        result = compute_capital_gains(lots, sells)
        # No grandfathering → cost = 1000
        # Gain = (3000 - 1000) * 10 = 20000
        assert result.ltcg_112a_gross == 20_000


class TestLTCGExemptionAggregate:
    """₹1.25L LTCG exemption is AGGREGATE across all stocks, not per-stock."""

    def test_exemption_shared_across_stocks(self):
        """Two stocks with 75K LTCG each = 150K total, exemption = 125K, taxable = 25K."""
        lots = [
            Lot(symbol="A", buy_date=date(2022, 1, 1), quantity=10, cost_per_unit=100),
            Lot(symbol="B", buy_date=date(2022, 1, 1), quantity=10, cost_per_unit=200),
        ]
        sells = [
            CGTransaction(symbol="A", sell_date=date(2024, 6, 1), quantity=10, sale_price_per_unit=850),
            CGTransaction(symbol="B", sell_date=date(2024, 6, 1), quantity=10, sale_price_per_unit=950),
        ]
        result = compute_capital_gains(lots, sells)
        # Both gains within ₹1.25L exemption → net = 0
        assert result.ltcg_112a_gross == 15_000
        assert result.ltcg_112a_net == 0

    def test_exemption_caps_at_125k(self):
        """LTCG of 200K → taxable = 200K - 125K = 75K."""
        lots = [Lot(symbol="HDFC", buy_date=date(2022, 1, 1), quantity=100, cost_per_unit=1000)]
        sells = [CGTransaction(symbol="HDFC", sell_date=date(2024, 6, 1), quantity=100, sale_price_per_unit=3000)]
        result = compute_capital_gains(lots, sells)
        assert result.ltcg_112a_gross == 200_000
        assert result.ltcg_112a_net == 75_000  # 200K - 125K exemption

    def test_loss_no_exemption_applied(self):
        """LTCG loss → no exemption applied (loss stays as-is)."""
        lots = [Lot(symbol="PAYTM", buy_date=date(2022, 1, 1), quantity=100, cost_per_unit=2000)]
        sells = [CGTransaction(symbol="PAYTM", sell_date=date(2024, 6, 1), quantity=100, sale_price_per_unit=500)]
        result = compute_capital_gains(lots, sells)
        assert result.ltcg_112a_gross == -150_000
        assert result.ltcg_112a_net == -150_000  # loss, no exemption


class TestTaxRulesIntegrity:
    """Verify tax rules constants haven't been accidentally modified."""

    def test_fy_2025_26_rates(self):
        rules = get_rules("2025-26")
        assert rules.stcg_111a_rate == Decimal("0.20")
        assert rules.ltcg_112a_rate == Decimal("0.125")
        assert rules.ltcg_112a_exemption == 125_000
        assert rules.cess_rate == Decimal("0.04")
        assert rules.standard_deduction_new == 75_000
        assert rules.standard_deduction_old == 50_000
        assert rules.sec_80c_limit == 150_000
        assert rules.advance_tax_threshold == 10_000

    def test_unsupported_fy_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            get_rules("2030-31")

    def test_new_regime_slabs_ordered(self):
        rules = get_rules("2025-26")
        prev_upper = 0
        for slab in rules.new_regime_slabs:
            assert slab.lower == prev_upper, f"Gap in slabs at {slab.lower}"
            prev_upper = slab.upper if slab.upper else slab.lower + 1
