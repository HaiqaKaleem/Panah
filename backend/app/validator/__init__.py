"""
Deterministic Validation Engine — public API.

Usage:
    from app.validator import validate_design, build_context

    context = build_context(design, constraints, analysis)
    report = validate_design(context)
    print(report.overall_status)  # "pass", "fail", "review", "error"
    print(report.to_dict())       # full structured output
"""

from .context import ValidationContext, build_context
from .engine import ValidationEngine
from .result import RuleResult, RuleType, Severity, ValidationReport, Verdict

_engine = ValidationEngine()


def validate_design(
    context: ValidationContext,
    rule_ids: list[str] | None = None,
) -> ValidationReport:
    """
    Run deterministic validation rules against a design.

    Args:
        context: Built via build_context() — contains design, constraints, analysis.
        rule_ids: Optional subset of rule IDs to evaluate. None = all rules.

    Returns:
        ValidationReport with per-rule results and overall status.
    """
    return _engine.validate(context, rule_ids=rule_ids)


def reload_rules():
    """Force the engine to reload YAML rule definitions from disk."""
    _engine.reload_rules()


def list_rules() -> list[str]:
    """Return all registered rule IDs."""
    return sorted(_engine.rules.keys())


__all__ = [
    "validate_design",
    "build_context",
    "ValidationContext",
    "ValidationEngine",
    "ValidationReport",
    "RuleResult",
    "RuleType",
    "Severity",
    "Verdict",
    "reload_rules",
    "list_rules",
]
