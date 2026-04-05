"""
Form 16 PDF Parser — Extract salary breakup, deductions, TDS.

Handles multiple Form 16 uploads. Standard deduction applied ONCE in tax engine.
Always returns parsed data for user confirmation — never silently trust.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pdfplumber


@dataclass
class Form16PartA:
    tan: str = ""
    employer_name: str = ""
    employer_pan: str = ""
    employee_pan: str = ""
    period_from: str = ""
    period_to: str = ""
    quarterly_tds: dict[str, int] = field(default_factory=dict)  # Q1-Q4
    total_tds: int = 0


@dataclass
class Form16PartB:
    gross_salary: int = 0
    basic: int = 0
    da: int = 0
    hra_received: int = 0
    lta: int = 0
    special_allowance: int = 0
    perquisites: int = 0
    employer_pf: int = 0
    employee_pf: int = 0
    professional_tax: int = 0
    standard_deduction: int = 0
    taxable_income_employer: int = 0
    # Deductions reported by employer
    sec_80c: int = 0
    sec_80d: int = 0
    sec_80ccd_1b: int = 0
    sec_80ccd_2: int = 0
    sec_80e: int = 0
    sec_80g: int = 0
    sec_80tta: int = 0
    total_deductions: int = 0
    # Tax computed by employer
    tax_on_income: int = 0
    rebate_87a: int = 0
    surcharge: int = 0
    cess: int = 0
    total_tax: int = 0


@dataclass
class Form16Result:
    part_a: Form16PartA = field(default_factory=Form16PartA)
    part_b: Form16PartB = field(default_factory=Form16PartB)
    confidence: float = 0.0  # 0-1, warn if < 0.8
    raw_text: str = ""
    warnings: list[str] = field(default_factory=list)


def _extract_amount(text: str, pattern: str) -> int:
    """Extract numeric amount following a pattern."""
    match = re.search(pattern + r"[\s:₹]*([0-9,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if match:
        return int(float(match.group(1).replace(",", "")))
    return 0


def _extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern + r"[\s:]*(.+?)(?:\n|$)", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def parse_form16(pdf_path: str, password: Optional[str] = None) -> Form16Result:
    """
    Parse Form 16 PDF. Returns structured data with confidence score.
    Caller MUST show parsed data for user confirmation.
    """
    result = Form16Result()
    try:
        pdf = pdfplumber.open(pdf_path, password=password)
    except Exception as e:
        result.warnings.append(f"Cannot open PDF: {e}")
        return result

    full_text = ""
    with pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"

    result.raw_text = full_text
    if not full_text.strip():
        result.warnings.append("PDF appears empty or is image-based. Please enter data manually.")
        return result

    # Part A
    a = result.part_a
    a.tan = _extract_field(full_text, r"TAN\s*(?:of|:)")
    a.employer_name = _extract_field(full_text, r"Name\s*(?:of|:)\s*(?:the\s+)?(?:Deductor|Employer)")
    a.employer_pan = _extract_field(full_text, r"PAN\s*(?:of|:)\s*(?:the\s+)?(?:Deductor|Employer)")
    a.employee_pan = _extract_field(full_text, r"PAN\s*(?:of|:)\s*(?:the\s+)?(?:Employee|Deductee)")

    # Quarterly TDS
    for q_label, q_key in [("Q1", "Q1"), ("Q2", "Q2"), ("Q3", "Q3"), ("Q4", "Q4")]:
        amt = _extract_amount(full_text, rf"(?:Quarter|{q_label}).*?(?:Amount|Tax)")
        if amt:
            a.quarterly_tds[q_key] = amt

    a.total_tds = _extract_amount(full_text, r"Total\s*(?:Tax\s*)?(?:Deducted|TDS)")
    if not a.total_tds and a.quarterly_tds:
        a.total_tds = sum(a.quarterly_tds.values())

    # Part B
    b = result.part_b
    b.gross_salary = _extract_amount(full_text, r"Gross\s*(?:Total\s*)?Salary")
    b.hra_received = _extract_amount(full_text, r"(?:House\s*Rent|HRA)\s*(?:Allowance)?")
    b.lta = _extract_amount(full_text, r"(?:Leave\s*Travel|LTA)")
    b.professional_tax = _extract_amount(full_text, r"(?:Professional|Profession)\s*Tax")
    b.standard_deduction = _extract_amount(full_text, r"Standard\s*Deduction")
    b.employer_pf = _extract_amount(full_text, r"Employer.*?(?:PF|Provident)")
    b.employee_pf = _extract_amount(full_text, r"Employee.*?(?:PF|Provident)")

    # Deductions
    b.sec_80c = _extract_amount(full_text, r"(?:80C|80\s*C)\b")
    b.sec_80d = _extract_amount(full_text, r"(?:80D|80\s*D)\b")
    b.sec_80ccd_1b = _extract_amount(full_text, r"80CCD\s*\(?1B\)?")
    b.sec_80ccd_2 = _extract_amount(full_text, r"80CCD\s*\(?2\)?")
    b.sec_80e = _extract_amount(full_text, r"(?:80E|80\s*E)\b")

    # Tax
    b.taxable_income_employer = _extract_amount(full_text, r"(?:Total\s*)?Taxable\s*Income")
    b.tax_on_income = _extract_amount(full_text, r"Tax\s*(?:on|payable\s*on)\s*(?:Total\s*)?Income")
    b.rebate_87a = _extract_amount(full_text, r"(?:Rebate|87A)")
    b.surcharge = _extract_amount(full_text, r"Surcharge")
    b.cess = _extract_amount(full_text, r"(?:Cess|Health.*Education)")
    b.total_tax = _extract_amount(full_text, r"(?:Net\s*)?Tax\s*Payable")

    # Confidence score
    fields_found = sum(
        1
        for v in [
            a.tan,
            a.employer_name,
            b.gross_salary,
            b.professional_tax,
            b.standard_deduction,
            a.total_tds,
            b.taxable_income_employer,
        ]
        if v
    )
    result.confidence = fields_found / 7

    if result.confidence < 0.8:
        result.warnings.append(f"Low confidence ({result.confidence:.0%}). Please verify all fields manually.")

    return result


def aggregate_form16s(results: list[Form16Result]) -> dict:
    """
    Aggregate multiple Form 16s. Standard deduction applied ONCE in tax engine.
    Returns combined salary details + total TDS.
    """
    combined = {
        "gross_salary": 0,
        "hra_received": 0,
        "lta": 0,
        "professional_tax": 0,
        "employer_pf": 0,
        "employee_pf": 0,
        "total_tds": 0,
        "form16_count": len(results),
        "employers": [],
    }
    for r in results:
        combined["gross_salary"] += r.part_b.gross_salary
        combined["hra_received"] += r.part_b.hra_received
        combined["lta"] += r.part_b.lta
        combined["professional_tax"] += r.part_b.professional_tax
        combined["employer_pf"] += r.part_b.employer_pf
        combined["employee_pf"] += r.part_b.employee_pf
        combined["total_tds"] += r.part_a.total_tds
        combined["employers"].append(
            {
                "name": r.part_a.employer_name,
                "tan": r.part_a.tan,
                "tds": r.part_a.total_tds,
            }
        )
    return combined
