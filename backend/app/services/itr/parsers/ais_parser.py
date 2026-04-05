"""
AIS (Annual Information Statement) PDF Parser.

Extracts all income categories, creates AISLineItem-compatible dicts.
Password hint: PAN lowercase + DOB (DDMMYYYY).
Flags exempt items, FD accrual, joint accounts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pdfplumber

# AIS section code → category mapping
_SECTION_MAP = {
    "192": ("TDS", "Salary"),
    "194A": ("TDS", "Interest other than securities"),
    "194": ("TDS", "Dividend"),
    "194B": ("TDS", "Lottery/crossword"),
    "194C": ("TDS", "Contractor payment"),
    "194H": ("TDS", "Commission/brokerage"),
    "194I": ("TDS", "Rent"),
    "194J": ("TDS", "Professional fees"),
    "194K": ("TDS", "MF income"),
    "194N": ("TDS", "Cash withdrawal"),
    "194Q": ("TCS", "Purchase of goods"),
    "206C": ("TCS", "TCS on various"),
}

_EXEMPT_KEYWORDS = frozenset(
    {
        "PPF",
        "PUBLIC PROVIDENT",
        "EPF",
        "EMPLOYEES PROVIDENT",
        "INSURANCE MATURITY",
        "LIC MATURITY",
        "SUKANYA",
    }
)


@dataclass
class AISEntry:
    info_code: str = ""
    description: str = ""
    source_name: str = ""
    source_tan: str = ""
    reported_value: int = 0
    modified_value: int = 0
    category: str = "other"
    is_exempt: bool = False
    flags: list[str] = field(default_factory=list)


@dataclass
class AISParseResult:
    entries: list[AISEntry] = field(default_factory=list)
    password_hint: str = "PAN (lowercase) + DOB (DDMMYYYY), e.g. abcde1234f01011990"
    raw_text: str = ""
    warnings: list[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


def parse_ais(pdf_path: str, password: Optional[str] = None) -> AISParseResult:
    """Parse AIS PDF and extract all income/transaction entries."""
    result = AISParseResult()

    try:
        pdf = pdfplumber.open(pdf_path, password=password)
    except Exception as e:
        if "password" in str(e).lower():
            result.warnings.append(f"PDF is password-protected. Hint: {result.password_hint}")
        else:
            result.warnings.append(f"Cannot open PDF: {e}")
        return result

    full_text = ""
    with pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"

    result.raw_text = full_text
    if not full_text.strip():
        result.warnings.append("PDF appears empty. Please enter data manually.")
        return result

    # Parse entries — look for structured rows with amounts
    # AIS format: Info Code | Description | Source | TAN | Reported | Modified
    lines = full_text.split("\n")
    current_entry: Optional[AISEntry] = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try to match section codes (e.g., "192", "194A")
        section_match = re.match(r"^(\d{3}[A-Z]?)\b", line)
        if section_match:
            if current_entry and (current_entry.reported_value or current_entry.description):
                result.entries.append(current_entry)

            code = section_match.group(1)
            cat_info = _SECTION_MAP.get(code, ("other", ""))
            current_entry = AISEntry(info_code=code, category=cat_info[0])
            # Extract rest of line
            rest = line[section_match.end() :].strip()
            if rest:
                current_entry.description = rest
            continue

        # Extract amounts from lines
        amounts = re.findall(r"₹?\s*([0-9,]+(?:\.\d{2})?)", line)
        if amounts and current_entry:
            values = [int(float(a.replace(",", ""))) for a in amounts]
            if len(values) >= 2:
                current_entry.reported_value = values[0]
                current_entry.modified_value = values[1]
            elif len(values) == 1:
                if not current_entry.reported_value:
                    current_entry.reported_value = values[0]

        # Extract TAN
        tan_match = re.search(r"[A-Z]{4}[0-9]{5}[A-Z]", line)
        if tan_match and current_entry:
            current_entry.source_tan = tan_match.group()

        # Source name (deductor)
        if current_entry and not current_entry.source_name:
            name_match = re.search(r"(?:M/s|Mr|Mrs|Ms)\.?\s*(.+?)(?:\s{2,}|\t|$)", line)
            if name_match:
                current_entry.source_name = name_match.group(1).strip()

    # Don't forget last entry
    if current_entry and (current_entry.reported_value or current_entry.description):
        result.entries.append(current_entry)

    # Post-processing: flag exempt items, FD interest, joint accounts
    for entry in result.entries:
        desc_upper = (entry.description + " " + entry.source_name).upper()

        # Exempt items
        if any(kw in desc_upper for kw in _EXEMPT_KEYWORDS):
            entry.is_exempt = True
            entry.flags.append("Potentially exempt income (PPF/EPF/insurance)")

        # FD interest
        if entry.info_code == "194A" or "FIXED DEPOSIT" in desc_upper or "FD" in desc_upper:
            entry.flags.append(
                "FD interest is taxable when accrued, not when received. "
                "Verify amount matches your FD interest certificates."
            )

        # Dividend — ensure gross
        if entry.info_code == "194":
            entry.flags.append(
                "Ensure this is the GROSS dividend amount (before TDS). "
                "Report gross amount in ITR, claim TDS separately."
            )

        # Joint account hint
        if "JOINT" in desc_upper:
            entry.flags.append("Joint account detected. Enter your share percentage.")

    # Summary
    result.summary = {
        "total_entries": len(result.entries),
        "tds_entries": sum(1 for e in result.entries if e.category == "TDS"),
        "tcs_entries": sum(1 for e in result.entries if e.category == "TCS"),
        "exempt_entries": sum(1 for e in result.entries if e.is_exempt),
        "total_reported": sum(e.reported_value for e in result.entries),
    }

    return result
