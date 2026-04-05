"""
ITR JSON Generator — Produces ITR-1/ITR-2 JSON matching official e-filing schema.

Includes Schedule 112A, Schedule CG, and all required schedules.
"""

from __future__ import annotations

import json


def generate_itr_json(
    profile: dict,
    computation: dict,
    cg_summary: dict | None = None,
    itr_form: str = "ITR-2",
) -> dict:
    """
    Generate ITR JSON structure. Returns dict ready for json.dumps().
    profile: TaxProfile as dict
    computation: TaxResult as dict
    cg_summary: CGSummary as dict
    """
    fy = profile.get("financial_year", "2025-26")
    ay = profile.get("assessment_year", "2026-27")
    regime = profile.get("regime_choice", "new")
    salary = profile.get("salary", {})
    ded = profile.get("deductions", {})
    other = profile.get("other_income", {})
    hp_list = profile.get("house_property", [])
    exempt = profile.get("exempt_income", {})
    cg = cg_summary or {}

    itr = {
        "form_type": itr_form,
        "financial_year": fy,
        "assessment_year": ay,
        "filing_status": "original",
        "regime": "new_115bac" if regime == "new" else "old",
        "personal_info": {
            "residency": profile.get("residency", "resident"),
            "age_category": profile.get("age_category", "normal"),
        },
        "income": {
            "salary": {
                "gross_salary": salary.get("gross", 0),
                "standard_deduction": computation.get("salary_income", 0) - salary.get("gross", 0),
                "net_salary": computation.get("salary_income", 0),
            },
            "house_property": [
                {
                    "type": hp.get("hp_type", "self_occupied"),
                    "gross_rent": hp.get("rental_income", 0),
                    "municipal_tax": hp.get("municipal_tax", 0),
                    "interest": hp.get("interest_paid", 0),
                }
                for hp in hp_list
            ],
            "other_sources": {
                "savings_interest": other.get("savings_interest", 0),
                "fd_interest": other.get("fd_interest", 0),
                "dividend": other.get("dividend_income_gross", 0),
                "other": other.get("other", 0),
            },
        },
        "deductions_via": {
            "sec_80c": ded.get("sec_80c", 0),
            "sec_80ccd_1b": ded.get("sec_80ccd_1b", 0),
            "sec_80ccd_2": ded.get("sec_80ccd_2", 0),
            "sec_80d": ded.get("sec_80d_self", 0) + ded.get("sec_80d_parents", 0),
            "sec_80e": ded.get("sec_80e", 0),
            "sec_80g": ded.get("sec_80g", 0),
            "sec_80tta": ded.get("sec_80tta", 0),
            "sec_80ttb": ded.get("sec_80ttb", 0),
            "total": computation.get("total_deductions", 0),
        },
        "exempt_income": {
            "ppf": exempt.get("ppf_maturity", 0),
            "epf": exempt.get("epf_withdrawal", 0),
            "agricultural": exempt.get("agricultural_income", 0),
        },
        "tax_computation": {
            "gross_total_income": computation.get("gross_total_income", 0),
            "total_deductions": computation.get("total_deductions", 0),
            "taxable_normal_income": computation.get("taxable_normal_income", 0),
            "tax_on_normal": computation.get("tax_on_normal", 0),
            "tax_stcg_111a": computation.get("tax_stcg_111a", 0),
            "tax_ltcg_112a": computation.get("tax_ltcg_112a", 0),
            "tax_ltcg_other": computation.get("tax_ltcg_other", 0),
            "rebate_87a": computation.get("rebate_87a", 0),
            "surcharge": computation.get("surcharge_normal", 0) + computation.get("surcharge_cg", 0),
            "cess": computation.get("cess", 0),
            "gross_tax": computation.get("gross_tax", 0),
            "tds": computation.get("total_tax_paid", 0),
            "interest_234b": computation.get("interest_234b", 0),
            "interest_234c": computation.get("interest_234c", 0),
            "late_fee_234f": computation.get("late_fee_234f", 0),
            "net_payable": computation.get("net_tax_payable", 0),
        },
    }

    # Schedule CG (ITR-2 only)
    if itr_form == "ITR-2" and cg:
        itr["schedule_cg"] = {
            "stcg_111a": cg.get("stcg_111a", 0),
            "stcg_other": cg.get("stcg_other", 0),
            "ltcg_112a_gross": cg.get("ltcg_112a_gross", 0),
            "ltcg_112a_exemption": min(cg.get("ltcg_112a_gross", 0), 125_000),
            "ltcg_112a_net": cg.get("ltcg_112a_net", 0),
            "ltcg_other": cg.get("ltcg_other", 0),
        }

        # Schedule 112A
        itr["schedule_112a"] = [
            {
                "isin": e.get("isin", ""),
                "scrip_name": e.get("scrip_name", ""),
                "quantity": e.get("quantity", 0),
                "sale_consideration": e.get("sale_consideration", 0),
                "cost_of_acquisition": e.get("cost_of_acquisition", 0),
                "fmv_31jan2018": e.get("fmv_31jan2018", 0),
                "ltcg": e.get("ltcg", 0),
            }
            for e in cg.get("schedule_112a", [])
        ]

    return itr


def export_json(itr_data: dict) -> str:
    """Serialize ITR data to JSON string."""
    return json.dumps(itr_data, indent=2, default=str)
