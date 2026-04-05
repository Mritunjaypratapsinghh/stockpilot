"""
Form 26AS PDF Parser — Source of truth for TDS credit claims.

Extracts Part A (TDS salary/other), Part A1 (non-salary), Part A2 (property sale),
Part B (TCS), Part C (tax paid), Part D (refunds).
If TDS not in 26AS, it CANNOT be claimed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pdfplumber


@dataclass
class TDS26ASEntry:
    tan: str = ""
    deductor_name: str = ""
    section: str = ""
    amount: int = 0
    date_of_credit: str = ""
    part: str = ""  # A, A1, A2


@dataclass
class TCSEntry:
    collector_tan: str = ""
    collector_name: str = ""
    amount: int = 0
    section: str = ""


@dataclass
class TaxPaidEntry:
    bsr_code: str = ""
    challan_date: str = ""
    challan_no: str = ""
    amount: int = 0
    tax_type: str = ""  # advance / self_assessment


@dataclass
class RefundEntry:
    assessment_year: str = ""
    amount: int = 0
    date_of_issue: str = ""


@dataclass
class Form26ASResult:
    tds_entries: list[TDS26ASEntry] = field(default_factory=list)
    tcs_entries: list[TCSEntry] = field(default_factory=list)
    tax_paid: list[TaxPaidEntry] = field(default_factory=list)
    refunds: list[RefundEntry] = field(default_factory=list)
    total_tds: int = 0
    total_tcs: int = 0
    total_advance_tax: int = 0
    total_self_assessment: int = 0
    raw_text: str = ""
    warnings: list[str] = field(default_factory=list)


def _extract_amounts(line: str) -> list[int]:
    return [int(float(m.replace(",", ""))) for m in re.findall(r"([0-9,]+(?:\.\d{2})?)", line)]


def parse_form26as(pdf_path: str, password: Optional[str] = None) -> Form26ASResult:
    """Parse Form 26AS PDF. This is the ONLY source for TDS credit claims."""
    result = Form26ASResult()

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
        result.warnings.append("PDF appears empty. Download 26AS from TRACES portal.")
        return result

    lines = full_text.split("\n")
    current_part = ""

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Detect parts
        line_upper = line_stripped.upper()
        if "PART A" in line_upper and "PART A1" not in line_upper and "PART A2" not in line_upper:
            current_part = "A"
            continue
        elif "PART A1" in line_upper:
            current_part = "A1"
            continue
        elif "PART A2" in line_upper:
            current_part = "A2"
            continue
        elif "PART B" in line_upper:
            current_part = "B"
            continue
        elif "PART C" in line_upper:
            current_part = "C"
            continue
        elif "PART D" in line_upper:
            current_part = "D"
            continue

        # Extract TAN pattern
        tan_match = re.search(r"([A-Z]{4}[0-9]{5}[A-Z])", line_stripped)

        # Part A/A1/A2: TDS entries
        if current_part in ("A", "A1", "A2") and tan_match:
            amounts = _extract_amounts(line_stripped)
            if amounts:
                entry = TDS26ASEntry(
                    tan=tan_match.group(1),
                    amount=amounts[-1],  # last amount is usually TDS
                    part=current_part,
                )
                # Try to extract section
                sec_match = re.search(r"(\d{3}[A-Z]?)\b", line_stripped)
                if sec_match and sec_match.group(1) != tan_match.group(1)[:3]:
                    entry.section = sec_match.group(1)
                # Deductor name: text before TAN
                name_part = line_stripped[: tan_match.start()].strip()
                if name_part:
                    entry.deductor_name = name_part
                result.tds_entries.append(entry)

        # Part B: TCS
        elif current_part == "B" and tan_match:
            amounts = _extract_amounts(line_stripped)
            if amounts:
                result.tcs_entries.append(
                    TCSEntry(
                        collector_tan=tan_match.group(1),
                        amount=amounts[-1],
                    )
                )

        # Part C: Tax paid
        elif current_part == "C":
            amounts = _extract_amounts(line_stripped)
            if amounts and len(amounts) >= 1:
                entry = TaxPaidEntry(amount=amounts[-1])
                if "ADVANCE" in line_upper:
                    entry.tax_type = "advance"
                elif "SELF" in line_upper or "ASSESSMENT" in line_upper:
                    entry.tax_type = "self_assessment"
                result.tax_paid.append(entry)

        # Part D: Refunds
        elif current_part == "D":
            amounts = _extract_amounts(line_stripped)
            if amounts:
                result.refunds.append(RefundEntry(amount=amounts[-1]))

    # Totals
    result.total_tds = sum(e.amount for e in result.tds_entries)
    result.total_tcs = sum(e.amount for e in result.tcs_entries)
    result.total_advance_tax = sum(e.amount for e in result.tax_paid if e.tax_type == "advance")
    result.total_self_assessment = sum(e.amount for e in result.tax_paid if e.tax_type == "self_assessment")

    if not result.tds_entries:
        result.warnings.append("No TDS entries found. Verify PDF format or enter manually.")

    return result
