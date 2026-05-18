"""Tests for FIFO capital gains engine."""

from datetime import date

from app.services.itr.capital_gains import (
    CGTransaction,
    Lot,
    _held_longer_than,
    compute_capital_gains,
)


class TestHoldingPeriod:
    """Exact date-level holding period classification."""

    def test_exactly_12_months_is_short_term(self):
        # Buy Jan 15, sell Jan 15 next year = exactly 12 months = NOT long term
        assert _held_longer_than(date(2024, 1, 15), date(2025, 1, 15), 12) is False

    def test_12_months_plus_one_day_is_long_term(self):
        assert _held_longer_than(date(2024, 1, 15), date(2025, 1, 16), 12) is True

    def test_11_months_is_short_term(self):
        assert _held_longer_than(date(2024, 1, 15), date(2025, 1, 14), 12) is False

    def test_leap_year_feb29(self):
        # Buy Feb 29 2024, hold 12 months → cutoff is Feb 28 2025 (no Feb 29)
        assert _held_longer_than(date(2024, 2, 29), date(2025, 3, 1), 12) is True
        assert _held_longer_than(date(2024, 2, 29), date(2025, 2, 28), 12) is False

    def test_24_month_threshold(self):
        # Debt MF: 24 months
        assert _held_longer_than(date(2022, 6, 1), date(2024, 6, 2), 24) is True
        assert _held_longer_than(date(2022, 6, 1), date(2024, 6, 1), 24) is False


class TestFIFO:
    """FIFO lot matching."""

    def test_single_buy_single_sell(self):
        lots = [Lot(symbol="TCS", buy_date=date(2023, 1, 1), quantity=10, cost_per_unit=3000)]
        sells = [CGTransaction(symbol="TCS", sell_date=date(2024, 6, 1), quantity=10, sale_price_per_unit=4000)]
        result = compute_capital_gains(lots, sells)
        # Gain = (4000-3000) * 10 = 10000, held > 12 months → LTCG 112A
        assert result.ltcg_112a_gross == 10_000

    def test_fifo_order(self):
        lots = [
            Lot(symbol="INFY", buy_date=date(2022, 1, 1), quantity=5, cost_per_unit=1000),
            Lot(symbol="INFY", buy_date=date(2023, 6, 1), quantity=5, cost_per_unit=1500),
        ]
        sells = [CGTransaction(symbol="INFY", sell_date=date(2024, 7, 1), quantity=7, sale_price_per_unit=2000)]
        result = compute_capital_gains(lots, sells)
        # FIFO: first 5 from lot1 (cost 1000), then 2 from lot2 (cost 1500)
        # Lot1: (2000-1000)*5 = 5000 (held >12m → LTCG)
        # Lot2: (2000-1500)*2 = 1000 (held >12m → LTCG)
        assert result.ltcg_112a_gross == 6_000

    def test_partial_sell(self):
        lots = [Lot(symbol="RELIANCE", buy_date=date(2023, 1, 1), quantity=100, cost_per_unit=2500)]
        sells = [CGTransaction(symbol="RELIANCE", sell_date=date(2023, 6, 1), quantity=30, sale_price_per_unit=2700)]
        result = compute_capital_gains(lots, sells)
        # Held < 12 months → STCG 111A
        # Gain = (2700-2500)*30 = 6000
        assert result.stcg_111a == 6_000

    def test_loss_scenario(self):
        lots = [Lot(symbol="PAYTM", buy_date=date(2023, 1, 1), quantity=50, cost_per_unit=1000)]
        sells = [CGTransaction(symbol="PAYTM", sell_date=date(2023, 8, 1), quantity=50, sale_price_per_unit=500)]
        result = compute_capital_gains(lots, sells)
        # Loss = (500-1000)*50 = -25000
        assert result.stcg_111a == -25_000
        assert result.total_stcl == 25_000

    def test_ltcg_exemption_applied(self):
        lots = [Lot(symbol="HDFC", buy_date=date(2022, 1, 1), quantity=100, cost_per_unit=1000)]
        sells = [CGTransaction(symbol="HDFC", sell_date=date(2024, 6, 1), quantity=100, sale_price_per_unit=2000)]
        result = compute_capital_gains(lots, sells)
        # Gross LTCG = 100K, exemption = 125K → net = 0
        assert result.ltcg_112a_gross == 100_000
        assert result.ltcg_112a_net == 0  # within exemption

    def test_multiple_symbols_independent(self):
        lots = [
            Lot(symbol="TCS", buy_date=date(2023, 1, 1), quantity=10, cost_per_unit=3000),
            Lot(symbol="INFY", buy_date=date(2023, 1, 1), quantity=10, cost_per_unit=1500),
        ]
        sells = [
            CGTransaction(symbol="TCS", sell_date=date(2023, 6, 1), quantity=10, sale_price_per_unit=3500),
            CGTransaction(symbol="INFY", sell_date=date(2023, 6, 1), quantity=10, sale_price_per_unit=1800),
        ]
        result = compute_capital_gains(lots, sells)
        # TCS: (3500-3000)*10 = 5000 STCG
        # INFY: (1800-1500)*10 = 3000 STCG
        assert result.stcg_111a == 8_000

    def test_no_sells_returns_zero(self):
        lots = [Lot(symbol="TCS", buy_date=date(2023, 1, 1), quantity=10, cost_per_unit=3000)]
        result = compute_capital_gains(lots, [])
        assert result.stcg_111a == 0
        assert result.ltcg_112a_gross == 0


class TestDebtMF:
    """Debt MF post-Apr-2023 → slab rate."""

    def test_debt_mf_post_2023_slab_rate(self):
        lots = [
            Lot(symbol="HDFC_DEBT", buy_date=date(2023, 5, 1), quantity=100, cost_per_unit=100, asset_type="debt_mf")
        ]
        sells = [
            CGTransaction(
                symbol="HDFC_DEBT",
                sell_date=date(2024, 6, 1),
                quantity=100,
                sale_price_per_unit=110,
                asset_type="debt_mf",
            )
        ]
        result = compute_capital_gains(lots, sells)
        # Post-Apr-2023 debt MF → always slab rate regardless of holding period
        assert result.slab_rate_gains == 1_000
        assert result.stcg_111a == 0
        assert result.ltcg_112a_gross == 0
