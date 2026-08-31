"""Validation rule result types.

Every rule returns a RuleResult. The engine aggregates them into a ValidationReport.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuleType(str, Enum):
    GEOMETRY = "geometry"
    MATERIAL = "material"
    LOAD_PATH = "load_path"
    ENVIRONMENT = "environment"
    CONNECTION = "connection"


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    REVIEW = "review"
    ERROR = "error"


class Severity(str, Enum):
    HARD = "hard"          # Block if FAIL
    MANDATORY = "mandatory"  # Block if FAIL or not evaluated
    SOFT = "soft"          # Advisory, never blocks
    ERROR = "error"        # Engine error


@dataclass
class RuleResult:
    """Result from a single deterministic validation rule."""
    rule_id: str
    status: str  # "pass", "fail", "skip", "error"
    message: str
    severity: Severity = Severity.SOFT
    rule_name: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def blocking(self) -> bool:
        return self.severity in (Severity.HARD, Severity.MANDATORY) and self.status == "fail"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "status": self.status,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
            "passed": self.passed,
            "blocking": self.blocking,
            "source": f"validator/{self.severity.value}",
        }


class ValidationReport:
    """Aggregated report from running all rules against a context."""

    def __init__(self, results: list[RuleResult], rule_set_version: str = "1.0.0"):
        self.results = results
        self.rule_set_version = rule_set_version

        self.passed_count = sum(1 for r in results if r.status == "pass")
        self.failed_count = sum(1 for r in results if r.status == "fail")
        self.skipped_count = sum(1 for r in results if r.status == "skip")
        self.error_count = sum(1 for r in results if r.status == "error")
        self.blocking_count = sum(1 for r in results if r.blocking)

        self.total = len(results)
        self.has_blocking = self.blocking_count > 0

    @classmethod
    def from_results(cls, results: list[RuleResult], rule_set_version: str = "1.0.0") -> ValidationReport:
        return cls(results, rule_set_version)

    @property
    def overall_status(self) -> str:
        if self.error_count > 0:
            return "error"
        if self.failed_count > 0:
            return "fail"
        if self.skipped_count > 0:
            return "review"
        return "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "rule_set_version": self.rule_set_version,
            "summary": {
                "total": self.total,
                "passed": self.passed_count,
                "failed": self.failed_count,
                "skipped": self.skipped_count,
                "errors": self.error_count,
                "blocking": self.blocking_count,
            },
            "results": [r.to_dict() for r in self.results],
        }


# ------------------------------------------------------------------
# Legacy types (kept for backward compat with existing tests/services)
# ------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationResult:
    """Legacy structured result from one deterministic validation rule."""

    rule_id: str
    rule_type: RuleType
    severity: Severity
    title: str
    verdict: Verdict
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.verdict is Verdict.PASS

    @property
    def blocking(self) -> bool:
        return self.severity in (Severity.HARD, Severity.MANDATORY) and self.verdict is Verdict.FAIL

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "verdict": self.verdict.value,
            "status": self.verdict.value,
            "message": self.message,
            "evidence": self.evidence,
            "assumptions": self.assumptions,
            "passed": self.passed,
            "blocking": self.blocking,
            "source": f"validator/{self.rule_type.value}",
        }
