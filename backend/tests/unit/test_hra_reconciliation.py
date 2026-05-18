"""Tests for HRA calculator and reconciliation engine."""

from datetime import date

import pytest

from app.services.itr.hra_calculator import compute_hra
from app.services.itr.reconciliation import (
    MatchStatus,
    reconcile_tds,
    generate_report,
)


class TestHRA:
    """HRA exemption calculation."""

    def test_metro_city(self):
        r = compute_hra(basic_plus_da=600_000, hra_received=200_000,
                        rent_paid=240_000, city_name="Mumbai")
        assert r.is_metro is True
        # min(200K actual, 240K-60K=180K rent-10%, 300K 50%basic)
        assert r.exemption == 180_000

    def test_non_metro_city(self):
        r = compute_hra(basic_plus_da=600_000, hra_received=200_000,
                        rent_paid=240_000, city_name="Jaipur")
        assert r.is_metro is False
        # min(200K actual, 180K rent-10%, 240K 40%basic)
        assert r.exemption == 180_000

    def test_new_regime_returns_zero(self):
        r = compute_hra(basic_plus_da=600_000, hra_received=200_000,
                        rent_paid=240_000, city_name="Mumbai", regime="new")
        assert r.exemption == 0
        assert len(r.warnings) > 0

    def test_no_rent_returns_zero(self):
        r = compute_hra(basic_plus_da=600_000, hra_received=200_000,
                        rent_paid=0, city_name="Mumbai")
        assert r.exemption == 0

    def test_no_hra_component(self):
        r = compute_hra(basic_plus_da=600_000, hra_received=0,
                        rent_paid=120_000, city_name="Delhi")
        assert r.exemption == 0
        assert "80GG" in r.warnings[0]


class TestReconciliation:
    """TDS reconciliation — 3-way match."""

    def test_perfect_match(self):
        f26 = [{"tan": "ABCD12345E", "section": "192", "amount": 50000, "deductor_name": "Corp"}]
        ais = [{"tan": "ABCD12345E", "section": "192", "amount": 50000, "source_name": "Corp"}]
        items = reconcile_tds([], ais, f26)
        assert len(items) == 1
        assert items[0].status == MatchStatus.MATCHED

    def test_amount_mismatch(self):
        f26 = [{"tan": "ABCD12345E", "section": "192", "amount": 50000, "deductor_name": "Corp"}]
        ais = [{"tan": "ABCD12345E", "section": "192", "amount": 48000, "source_name": "Corp"}]
        items = reconcile_tds([], ais, f26)
        assert items[0].status == MatchStatus.AMOUNT_MISMATCH
        assert items[0].recommended_amount == 50000  # 26AS is truth

    def test_missing_in_26as(self):
        ais = [{"tan": "XXXX99999X", "section": "194A", "amount": 5000, "source_name": "Bank"}]
        items = reconcile_tds([], ais, [])
        assert items[0].status == MatchStatus.MISSING_IN_26AS
        assert items[0].recommended_amount == 0  # cannot claim

    def test_duplicate_entries_accumulated(self):
        f26 = [
            {"tan": "ABCD12345E", "section": "192", "amount": 25000, "deductor_name": "Corp"},
            {"tan": "ABCD12345E", "section": "192", "amount": 25000, "deductor_name": "Corp"},
            {"tan": "ABCD12345E", "section": "192", "amount": 25000, "deductor_name": "Corp"},
            {"tan": "ABCD12345E", "section": "192", "amount": 25000, "deductor_name": "Corp"},
        ]
        items = reconcile_tds([], [], f26)
        assert len(items) == 1
        assert items[0].form26as_amount == 100_000

    def test_report_blocks_on_pending_ais(self):
        report = generate_report([], [], pending_ais_count=5)
        assert report.can_proceed is False
        assert report.pending_ais_count == 5

    def test_report_allows_when_no_pending(self):
        report = generate_report([], [], pending_ais_count=0)
        assert report.can_proceed is True
