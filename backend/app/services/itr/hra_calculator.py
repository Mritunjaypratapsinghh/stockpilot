"""
HRA Exemption Calculator.

min(actual HRA, rent - 10% basic+DA, 50%/40% basic+DA) × months/12.
Only applicable in old regime.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tax_rules import TaxRules, get_rules


@dataclass
class HRAResult:
    exemption: int = 0
    actual_hra: int = 0
    rent_minus_10pct: int = 0
    metro_component: int = 0
    limiting_factor: str = ""
    is_metro: bool = False
    warnings: list[str] = field(default_factory=list)
    tip: str = ""


def compute_hra(
    basic_plus_da: int,
    hra_received: int,
    rent_paid: int,
    city_name: str,
    months: int = 12,
    regime: str = "old",
    has_home_loan_same_city: bool = False,
    rules: TaxRules | None = None,
) -> HRAResult:
    """Compute HRA exemption under Section 10(13A)."""
    rules = rules or get_rules()
    result = HRAResult()

    if regime == "new":
        result.warnings.append("HRA exemption is NOT available under new regime.")
        return result

    if hra_received <= 0:
        result.warnings.append("No HRA component in salary. Consider Section 80GG (max ₹5,000/month).")
        result.tip = f"80GG max deduction: ₹{rules.sec_80gg_monthly * 12:,}/year"
        return result

    if rent_paid <= 0:
        result.warnings.append("No rent paid — HRA exemption is zero.")
        return result

    is_metro = city_name.lower().strip() in rules.hra_metro_cities
    result.is_metro = is_metro
    rate = rules.hra_metro_rate if is_metro else rules.hra_non_metro_rate

    # Pro-rate for partial year
    factor = months / 12

    result.actual_hra = int(hra_received * factor)
    result.rent_minus_10pct = max(0, int((rent_paid - float(rules.hra_basic_rate) * basic_plus_da) * factor))
    result.metro_component = int(float(rate) * basic_plus_da * factor)

    components = [
        (result.actual_hra, "Actual HRA received"),
        (result.rent_minus_10pct, "Rent paid minus 10% of Basic+DA"),
        (result.metro_component, f"{'50%' if is_metro else '40%'} of Basic+DA"),
    ]
    min_val, min_label = min(components, key=lambda x: x[0])
    result.exemption = min_val
    result.limiting_factor = min_label

    # Warnings
    if rent_paid > 100_000 and months >= 12:
        result.warnings.append("Rent exceeds ₹1L/year — landlord PAN is mandatory.")

    if has_home_loan_same_city:
        result.warnings.append(
            "Claiming HRA + home loan interest in same city may be questioned. "
            "Ensure you have a valid reason (e.g., office distance)."
        )

    # Optimization tip
    if result.limiting_factor == "Actual HRA received":
        result.tip = "HRA component is the bottleneck. Negotiate higher HRA in salary structure."
    elif result.limiting_factor == "Rent paid minus 10% of Basic+DA":
        result.tip = "Increasing rent (with genuine receipts) would increase exemption."

    return result
