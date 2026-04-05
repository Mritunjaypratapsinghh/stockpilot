"""
Audit Trail Logger — Records every computed value with source, rule, and formula.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AuditEntry:
    step: str
    field_name: str
    computed_value: float
    source: str = ""
    rule_applied: str = ""
    formula: str = ""
    inputs: dict = field(default_factory=dict)


class AuditTrail:
    """Collects audit entries during tax computation."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def log(
        self,
        step: str,
        field_name: str,
        value: float,
        source: str = "computed",
        rule: str = "",
        formula: str = "",
        inputs: dict | None = None,
    ) -> None:
        self.entries.append(
            AuditEntry(
                step=step,
                field_name=field_name,
                computed_value=value,
                source=source,
                rule_applied=rule,
                formula=formula,
                inputs=inputs or {},
            )
        )

    def to_dicts(self) -> list[dict]:
        return [
            {
                "step": e.step,
                "field_name": e.field_name,
                "computed_value": e.computed_value,
                "source": e.source,
                "rule_applied": e.rule_applied,
                "formula": e.formula,
                "inputs": e.inputs,
            }
            for e in self.entries
        ]
