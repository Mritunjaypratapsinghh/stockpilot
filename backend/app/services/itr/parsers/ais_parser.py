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

# Regex to match AIS info code header lines.
# Codes can be: TDS-192, SFT-015, SFT-016(SB), SFT-016(TD), SFT-17-LES(M), SFT-18-EMF(M), etc.
_CODE_RE = re.compile(r"^(\d+)\s+((?:TDS|TCS|SFT)-[\w\-()]+(?:\([\w]+\))?)\s+(.+)")

# Amount at end of line after count: "COUNT AMOUNT" pattern
# The header line ends with: count amount (e.g., "9 9,27,816" or "1 53" or "14 34,537.00")
_HEADER_AMOUNT_RE = re.compile(r"\b(\d+)\s+([\d,]+(?:\.\d+)?)\s*$")


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
    # Capital gains detail
    sale_transactions: list[dict] = field(default_factory=list)


@dataclass
class AISParseResult:
    entries: list[AISEntry] = field(default_factory=list)
    password_hint: str = "PAN (lowercase) + DOB (DDMMYYYY), e.g. abcde1234f01011990"
    raw_text: str = ""
    warnings: list[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    personal_info: dict = field(default_factory=dict)


def _parse_amount(s: str) -> int:
    """Parse Indian formatted amount like '5,94,087' or '349.00' to int."""
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


def _extract_cg_amounts(raw: str, txn: dict) -> None:
    """Extract sale_consideration and cost_of_acquisition from a CG transaction line.

    After the Long/Short keyword, numbers follow this pattern:
    QTY PRICE SALE_CONSIDERATION [STT] COST ...
    """
    term_match = re.search(r"\b(Long|Short)\b", raw)
    if not term_match:
        return
    after_term = raw[term_match.end() :]
    nums = re.findall(r"([\d,]+\.\d+|[\d,]{2,})", after_term)
    parsed = [float(n.replace(",", "")) for n in nums]
    # idx 0=QTY, 1=PRICE, 2=SALE_CONSIDERATION, 3=STT or COST, 4=COST (if STT present)
    if len(parsed) >= 4:
        txn["sale_consideration"] = int(parsed[2])
        # If parsed[3] < 1, it's STT → cost is parsed[4]
        if parsed[3] < 1 and len(parsed) >= 5:
            txn["cost_of_acquisition"] = int(parsed[4])
        else:
            txn["cost_of_acquisition"] = int(parsed[3])


def _extract_header_amount(full_line: str) -> int:
    """
    Extract the AMOUNT from the end of a header line.
    Header lines end with: ... COUNT AMOUNT
    E.g.: "... KOGTA FINANCIAL (I) LTD (JPRK02037A) 9 9,27,816"
    We want 9,27,816 (not 9 which is the count).
    """
    m = _HEADER_AMOUNT_RE.search(full_line)
    if m:
        return _parse_amount(m.group(2))
    return 0


def parse_ais(pdf_path: str, password: Optional[str] = None) -> AISParseResult:
    """Parse AIS PDF and extract all income/transaction entries."""
    result = AISParseResult()

    # Try multiple password variants
    passwords_to_try = [password]
    if password:
        passwords_to_try.extend([password.lower(), password.upper()])
        passwords_to_try = list(dict.fromkeys(passwords_to_try))

    pdf = None
    for pw in passwords_to_try:
        try:
            pdf = pdfplumber.open(pdf_path, password=pw)
            break
        except Exception:
            continue

    if pdf is None:
        result.warnings.append(f"Cannot open PDF. Ensure password is correct. Hint: {result.password_hint}")
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

        # Match header line: "SR_NO INFO_CODE DESCRIPTION SOURCE (TAN) COUNT AMOUNT"
        code_match = _CODE_RE.match(line)
        if code_match:
            # Save previous entry
            if current_entry and (current_entry.reported_value or current_entry.description):
                result.entries.append(current_entry)

            info_code = code_match.group(2)
            rest = code_match.group(3)

            current_entry = AISEntry(
                info_code=info_code,
                category=_detect_category(info_code),
            )

            # Extract amount from rest FIRST (before combining with next line)
            current_entry.reported_value = _extract_header_amount(rest)

            # Check if next line is a continuation (has TAN but no code_match)
            full_rest = rest
            if i < len(lines):
                next_line = lines[i].strip()
                if (
                    next_line
                    and not _CODE_RE.match(next_line)
                    and re.search(r"\([A-Z]{4}[\dA-Z]{5}[A-Z](?:\.\w+)?\)", next_line)
                ):
                    full_rest += " " + next_line
                    i += 1

            # Extract source TAN from combined text
            tan_match = re.search(r"\(([A-Z]{4}[\dA-Z]{5}[A-Z](?:\.\w+)?)\)", full_rest)
            if tan_match:
                current_entry.source_tan = tan_match.group(1)
                before_tan = full_rest[: tan_match.start()].strip()
                current_entry.description = before_tan
            else:
                current_entry.description = full_rest.strip()

            continue

        # Capital gains transaction detail lines (for SFT-17/SFT-18 sales)
        if (
            current_entry
            and current_entry.info_code.upper().startswith("SFT-17")
            and "LES" in current_entry.info_code.upper()
        ):
            # Equity sale detail
            date_match = re.match(r"^\d+\s+(\d{2}/\d{2}/\d{4})\s+(.+)", line)
            if date_match:
                txn = {"raw": line, "date": date_match.group(1)}
                if "Long" in line:
                    txn["term"] = "long"
                elif "Short" in line:
                    txn["term"] = "short"
                _extract_cg_amounts(line, txn)
                current_entry.sale_transactions.append(txn)

        if current_entry and (
            "SFT-18-EMF" in current_entry.info_code.upper() or "SFT-17-OTU" in current_entry.info_code.upper()
        ):
            # MF / Other unit sale detail lines
            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", line)
            if date_match and ("Long" in line or "Short" in line):
                txn = {"raw": line, "date": date_match.group(1)}
                if "Long" in line:
                    txn["term"] = "long"
                elif "Short" in line:
                    txn["term"] = "short"
                _extract_cg_amounts(line, txn)
                current_entry.sale_transactions.append(txn)

    # Don't forget last entry
    if current_entry and (current_entry.reported_value or current_entry.description):
        result.entries.append(current_entry)

    # Post-processing: parse capital gains from sale transaction details
    _enrich_capital_gains(result.entries)

    # Post-processing flags
    for entry in result.entries:
        desc_upper = (entry.description + " " + entry.source_name).upper()
        if any(kw in desc_upper for kw in _EXEMPT_KEYWORDS):
            entry.is_exempt = True
            entry.flags.append("Potentially exempt income (PPF/EPF/insurance)")
        if "016(TD)" in entry.info_code or "194A" in entry.info_code or "FIXED DEPOSIT" in desc_upper:
            entry.flags.append("FD interest is taxable when accrued, not when received.")
        if "015" in entry.info_code or "DIVIDEND" in desc_upper:
            entry.flags.append("Ensure this is GROSS dividend (before TDS).")
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


def _enrich_capital_gains(entries: list[AISEntry]) -> None:
    """Tag capital gain entries with computed gain/loss from transactions."""
    for entry in entries:
        if not entry.sale_transactions:
            continue
        code = entry.info_code.upper()
        if "LES" in code or "EMF" in code or "OTU" in code:
            total_sale = 0
            total_cost = 0
            for txn in entry.sale_transactions:
                total_sale += txn.get("sale_consideration", 0)
                total_cost += txn.get("cost_of_acquisition", 0)
            if total_sale or total_cost:
                entry.flags.append(f"CG: Sale={total_sale}, Cost={total_cost}, Gain/Loss={total_sale - total_cost}")
