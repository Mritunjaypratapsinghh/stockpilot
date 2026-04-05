"""
AIS (Annual Information Statement) PDF Parser.

Parses the actual AIS PDF format from the Income Tax Compliance Portal.
Password hint: PAN lowercase + DOB (DDMMYYYY).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pdfplumber

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
    category: str = "other"  # TDS / TCS / SFT / tax_payment / other
    is_exempt: bool = False
    flags: list[str] = field(default_factory=list)
    quarters: list[dict] = field(default_factory=list)


@dataclass
class AISParseResult:
    entries: list[AISEntry] = field(default_factory=list)
    password_hint: str = "PAN (lowercase) + DOB (DDMMYYYY), e.g. abcde1234f01011990"
    raw_text: str = ""
    warnings: list[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    personal_info: dict = field(default_factory=dict)


def _parse_amount(s: str) -> int:
    """Parse Indian formatted amount like '5,94,087' to int."""
    s = s.strip().replace(",", "").replace("₹", "").strip()
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _detect_category(info_code: str) -> str:
    code = info_code.upper()
    if code.startswith("TDS"):
        return "TDS"
    if code.startswith("TCS"):
        return "TCS"
    if code.startswith("SFT"):
        return "SFT"
    if "TAX PAYMENT" in code or "ADVANCE TAX" in code:
        return "tax_payment"
    return "other"


def parse_ais(pdf_path: str, password: Optional[str] = None) -> AISParseResult:
    """Parse AIS PDF and extract all income/transaction entries."""
    result = AISParseResult()

    try:
        pdf = pdfplumber.open(pdf_path, password=password)
    except Exception as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
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

    # Extract personal info from Part A
    pan_match = re.search(r"([A-Z]{5}\d{4}[A-Z])\s+(?:XXXX|[\dX]+)", full_text)
    name_match = re.search(r"Name of Assessee\s*\n\s*[A-Z]{5}\d{4}[A-Z]\s+[\dX\s]+\s+(.+)", full_text)
    if pan_match:
        result.personal_info["pan"] = pan_match.group(1)
    if name_match:
        result.personal_info["name"] = name_match.group(1).strip()

    # Parse entries
    lines = full_text.split("\n")
    current_entry: Optional[AISEntry] = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue

        # Look for info code lines: "N TDS-192 ..." or "N SFT-18(Pur) ..."
        code_match = re.match(
            r"^\d+\s+((?:TDS|TCS|SFT)-[\w()]+)\s+(.+)",
            line,
        )
        if code_match:
            # Save previous entry
            if current_entry and (current_entry.reported_value or current_entry.description):
                result.entries.append(current_entry)

            info_code = code_match.group(1)
            rest = code_match.group(2)

            current_entry = AISEntry(
                info_code=info_code,
                category=_detect_category(info_code),
            )

            # Extract source name and TAN from rest or next lines
            # Pattern: "Description SOURCE (TAN) COUNT AMOUNT"
            tan_match = re.search(r"\(([A-Z]{4}[\dA-Z]{5}[A-Z](?:\.\w+)?)\)", rest)
            if tan_match:
                current_entry.source_tan = tan_match.group(1)
                # Description is before the source
                desc_part = rest[: tan_match.start()].strip()
                # Source name is the last part before TAN
                # Try to split description and source
                current_entry.description = desc_part
            else:
                current_entry.description = rest.strip()

            # Extract amount — last number on the line (skip small numbers like counts)
            amounts = re.findall(r"([\d,]{3,})", rest)
            if amounts:
                # Filter: take the largest amount (skip counts like "1", section numbers like "018")
                parsed = [_parse_amount(a) for a in amounts]
                # The actual amount is typically the last large number
                current_entry.reported_value = parsed[-1] if parsed else 0

            # Check next line for continuation (source name with TAN)
            if i < len(lines):
                next_line = lines[i].strip()
                tan_next = re.search(r"\(([A-Z]{4}[\dA-Z]{5}[A-Z](?:\.\w+)?)\)", next_line)
                if tan_next and not current_entry.source_tan:
                    current_entry.source_tan = tan_next.group(1)
                    current_entry.source_name = next_line[: tan_next.start()].strip()
                    # Only take amount from next line if we don't have one yet
                    if not current_entry.reported_value:
                        amounts_next = re.findall(r"\b(\d{1,3}(?:,\d{2,3})+)\b", next_line)
                        if amounts_next:
                            current_entry.reported_value = _parse_amount(amounts_next[-1])
                    i += 1

            continue

        # Look for quarter detail lines
        if current_entry and re.match(r"^\d+\s+Q[1-4]", line):
            quarter_info = {"raw": line}
            # Extract amounts from quarter lines
            amounts = re.findall(r"([\d,]{3,})", line)
            if amounts:
                quarter_info["amounts"] = [_parse_amount(a) for a in amounts]
            current_entry.quarters.append(quarter_info)

    # Don't forget last entry
    if current_entry and (current_entry.reported_value or current_entry.description):
        result.entries.append(current_entry)

    # Post-processing
    for entry in result.entries:
        desc_upper = (entry.description + " " + entry.source_name).upper()

        # Exempt items
        if any(kw in desc_upper for kw in _EXEMPT_KEYWORDS):
            entry.is_exempt = True
            entry.flags.append("Potentially exempt income (PPF/EPF/insurance)")

        # FD interest
        if "194A" in entry.info_code or "FIXED DEPOSIT" in desc_upper:
            entry.flags.append("FD interest is taxable when accrued, not when received.")

        # Dividend
        if "194" in entry.info_code and "194A" not in entry.info_code:
            entry.flags.append("Ensure this is GROSS dividend (before TDS).")

        # Salary
        if "192" in entry.info_code:
            entry.flags.append("Cross-verify with Form 16 from employer.")

    # Summary
    result.summary = {
        "total_entries": len(result.entries),
        "tds_entries": sum(1 for e in result.entries if e.category == "TDS"),
        "tcs_entries": sum(1 for e in result.entries if e.category == "TCS"),
        "sft_entries": sum(1 for e in result.entries if e.category == "SFT"),
        "exempt_entries": sum(1 for e in result.entries if e.is_exempt),
        "total_reported": sum(e.reported_value for e in result.entries),
    }

    return result
