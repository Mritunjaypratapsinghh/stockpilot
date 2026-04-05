"""
Tax Optimization Engine — Regime comparison + actionable suggestions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tax_engine import RegimeComparison, TaxInput, compare_regimes
from .tax_rules import TaxRules, get_rules


@dataclass
class Suggestion:
    category: str
    title: str
    description: str
    potential_saving: int = 0


@dataclass
class OptimizationResult:
    comparison: RegimeComparison | None = None
    suggestions: list[Suggestion] = field(default_factory=list)
    total_potential_saving: int = 0


def optimize(inp: TaxInput, rules: TaxRules | None = None) -> OptimizationResult:
    """Run regime comparison and generate optimization suggestions."""
    rules = rules or get_rules()
    result = OptimizationResult()
    result.comparison = compare_regimes(inp, rules)

    # Suggestion: 80C headroom
    if inp.sec_80c < rules.sec_80c_limit:
        gap = rules.sec_80c_limit - inp.sec_80c
        saving = int(gap * 0.3)  # approximate at 30% slab
        result.suggestions.append(
            Suggestion(
                "deduction",
                "Maximize 80C",
                f"₹{gap:,} headroom in 80C. Invest in ELSS/PPF/NPS to save ~₹{saving:,} (old regime).",
                saving,
            )
        )

    # Suggestion: 80CCD(1B)
    if inp.sec_80ccd_1b == 0:
        result.suggestions.append(
            Suggestion(
                "deduction",
                "NPS 80CCD(1B)",
                f"Invest up to ₹{rules.sec_80ccd_1b_limit:,} in NPS for additional deduction (old regime).",
                int(rules.sec_80ccd_1b_limit * 0.3),
            )
        )

    # Suggestion: 80D
    total_80d = inp.sec_80d_self + inp.sec_80d_parents
    if total_80d < rules.sec_80d_max:
        gap = rules.sec_80d_max - total_80d
        result.suggestions.append(
            Suggestion(
                "deduction",
                "Health Insurance 80D",
                f"₹{gap:,} headroom in 80D. Get health insurance for self/parents.",
                int(gap * 0.3),
            )
        )

    # Suggestion: HRA
    if inp.hra_exemption == 0 and inp.gross_salary > 0:
        result.suggestions.append(
            Suggestion(
                "salary",
                "Claim HRA",
                "If paying rent, claim HRA exemption (old regime). Can save significant tax.",
            )
        )

    # Suggestion: LTCG harvesting
    if inp.ltcg_112a_gross > 0 and inp.ltcg_112a_gross <= rules.ltcg_112a_exemption:
        result.suggestions.append(
            Suggestion(
                "capital_gains",
                "LTCG within exemption",
                f"Your LTCG (₹{inp.ltcg_112a_gross:,}) is within "
                f"₹{rules.ltcg_112a_exemption:,} exemption. Zero CG tax!",
            )
        )

    result.total_potential_saving = sum(s.potential_saving for s in result.suggestions)
    return result
