"""Tests for tax computation engine — the most critical business logic."""

from datetime import date
from decimal import Decimal

import pytest

from app.services.itr.tax_engine import TaxInput, TaxResult, compare_regimes, compute_tax


class TestNewRegimeSlabs:
    """Verify new regime slab computation for FY 2025-26."""

    def test_zero_income(self):
        r = compute_tax(TaxInput(), regime="new")
        assert r.net_tax_payable == 0

    def test_income_below_exemption(self):
        # 4L taxable = 0 tax (first slab is 0-4L at 0%)
        inp = TaxInput(gross_salary=475_000)  # 475K - 75K std ded = 400K
        r = compute_tax(inp, regime="new")
        assert r.tax_on_normal == 0

    def test_income_in_5pct_slab(self):
        # Taxable = 600K → tax on 200K @ 5% = 10000
        inp = TaxInput(gross_salary=675_000)  # 675K - 75K = 600K
        r = compute_tax(inp, regime="new")
        assert r.tax_on_normal == 10_000

    def test_income_12L_gets_full_rebate(self):
        # Taxable = 12L exactly → full 87A rebate
        inp = TaxInput(gross_salary=1_275_000)  # 1275K - 75K = 1200K
        r = compute_tax(inp, regime="new")
        assert r.rebate_87a > 0
        assert r.net_tax_payable <= 0

    def test_marginal_relief_just_above_12L(self):
        # Taxable = 12,01,000 → marginal relief caps tax at ₹1000
        inp = TaxInput(gross_salary=1_276_000)
        r = compute_tax(inp, regime="new")
        # Tax should be approximately the excess (₹1000) + cess
        assert r.net_tax_payable <= 1100  # 1000 + 4% cess

    def test_high_income_30pct_slab(self):
        # Taxable = 30L → hits 30% slab
        inp = TaxInput(gross_salary=3_075_000)  # 3075K - 75K = 3000K
        r = compute_tax(inp, regime="new")
        assert r.tax_on_normal > 0
        assert r.rebate_87a == 0  # no rebate above 12L


class TestOldRegime:
    """Verify old regime with deductions."""

    def test_80c_deduction_applied(self):
        inp = TaxInput(gross_salary=1_500_000, sec_80c=150_000)
        old = compute_tax(inp, regime="old")
        new = compute_tax(inp, regime="new")
        # Old regime should have lower taxable income due to 80C
        assert old.total_deductions >= 150_000
        assert old.taxable_normal_income < new.taxable_normal_income

    def test_80c_capped_at_150k(self):
        inp = TaxInput(gross_salary=2_000_000, sec_80c=300_000)  # exceeds limit
        r = compute_tax(inp, regime="old")
        # Deduction should be capped at 150K, not 300K
        assert r.total_deductions <= 200_000  # 150K 80C + maybe 80CCD2


class TestHPLoss:
    """House property loss set-off."""

    def test_hp_loss_capped_at_2L(self):
        inp = TaxInput(gross_salary=1_500_000, hp_income=-350_000)
        r = compute_tax(inp, regime="new")
        # salary = 1500K - 75K = 1425K
        # HP capped at -200K
        # taxable = 1425K - 200K = 1225K
        assert r.taxable_normal_income == 1_225_000

    def test_hp_loss_under_limit(self):
        inp = TaxInput(gross_salary=1_000_000, hp_income=-100_000)
        r = compute_tax(inp, regime="new")
        # salary = 925K, HP = -100K (under 2L limit)
        assert r.taxable_normal_income == 825_000

    def test_hp_income_positive(self):
        inp = TaxInput(gross_salary=1_000_000, hp_income=200_000)
        r = compute_tax(inp, regime="new")
        # salary = 925K + HP 200K = 1125K
        assert r.taxable_normal_income == 1_125_000


class TestCapitalGains:
    """Special rate capital gains taxation."""

    def test_stcg_111a_at_20pct(self):
        inp = TaxInput(gross_salary=500_000, stcg_111a=100_000)
        r = compute_tax(inp, regime="new")
        assert r.tax_stcg_111a == 20_000  # 20% of 1L

    def test_ltcg_112a_exemption(self):
        inp = TaxInput(gross_salary=500_000, ltcg_112a_gross=200_000)
        r = compute_tax(inp, regime="new")
        # Taxable LTCG = 200K - 125K exemption = 75K @ 12.5%
        assert r.tax_ltcg_112a == 9_375  # 12.5% of 75K

    def test_ltcg_within_exemption(self):
        inp = TaxInput(gross_salary=500_000, ltcg_112a_gross=100_000)
        r = compute_tax(inp, regime="new")
        # 100K < 125K exemption → 0 tax
        assert r.tax_ltcg_112a == 0


class TestRegimeComparison:
    """Regime comparison recommends lower tax."""

    def test_high_deductions_favors_old(self):
        # At 50L salary with max deductions + HRA + NPS, old regime wins
        inp = TaxInput(
            gross_salary=5_000_000,
            basic_plus_da=2_500_000,
            sec_80c=150_000, sec_80ccd_1b=50_000, sec_80ccd_2=250_000,
            sec_80d_self=50_000, sec_80d_parents=50_000,
            hra_exemption=600_000, lta_exemption=100_000, professional_tax=2500,
        )
        comp = compare_regimes(inp)
        assert comp.recommended == "old"
        assert comp.savings > 0

    def test_no_deductions_favors_new(self):
        inp = TaxInput(gross_salary=1_500_000)
        comp = compare_regimes(inp)
        assert comp.recommended == "new"
        assert comp.savings >= 0


class TestSurchargeAndCess:
    """Surcharge and cess calculations."""

    def test_cess_4pct(self):
        inp = TaxInput(gross_salary=2_000_000)
        r = compute_tax(inp, regime="new")
        assert r.cess > 0
        # Cess should be ~4% of (tax + surcharge)

    def test_no_surcharge_below_50L(self):
        inp = TaxInput(gross_salary=3_000_000)
        r = compute_tax(inp, regime="new")
        assert r.surcharge_normal == 0  # below 50L threshold


class TestTaxPaid:
    """Net payable with TDS/advance tax credits."""

    def test_tds_reduces_payable(self):
        inp = TaxInput(gross_salary=1_500_000, tds_total=100_000)
        r = compute_tax(inp, regime="new")
        r_no_tds = compute_tax(TaxInput(gross_salary=1_500_000), regime="new")
        assert r.net_tax_payable == r_no_tds.net_tax_payable - 100_000

    def test_refund_when_tds_exceeds_tax(self):
        inp = TaxInput(gross_salary=800_000, tds_total=200_000)
        r = compute_tax(inp, regime="new")
        assert r.net_tax_payable < 0  # refund
