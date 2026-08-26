
"""
Panah Standards & Rules Engine.

This module provides the deterministic standards-prescreening layer for Panah.

Design principles
-----------------
1. Standards are represented as structured, traceable rules.
2. Rule provenance is preserved so the UI can explain WHY a result exists.
3. Prescreening never pretends to be a full structural simulation.
4. Rules that require analysis data remain NOT_EVALUATED until that evidence
   is supplied.
5. The engine is deterministic and side-effect free.
6. The public API is intentionally small so other Panah layers can consume it.

The current rule catalog is derived from the Sphere Handbook V24.1
"Guideline & Standards" interface represented in the Panah frontend design,
particularly:

    Shelter standard 2: Structural Stability
    Technical Indicators
    Cross-bracing requirements

This module does not claim to contain the complete Sphere Handbook.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping

from app.constraints.schemas import ConstraintSet


# ---------------------------------------------------------------------------
# Result vocabulary
# ---------------------------------------------------------------------------


class RuleStatus(str, Enum):
    """Machine-readable outcome of an individual rule."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_EVALUATED = "not_evaluated"


class RuleSeverity(str, Enum):
    """Operational importance of a rule."""

    INFO = "info"
    WARNING = "warning"
    MANDATORY = "mandatory"


# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StandardRule:
    """
    Immutable definition of a Panah standards rule.

    The metadata is intentionally separate from evaluation evidence.
    This allows the frontend to display the standard itself independently
    from the current project's result.
    """

    rule_id: str
    title: str
    category: str
    requirement: str
    source: str
    section: str
    severity: RuleSeverity
    verification_source: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""
        payload = asdict(self)
        payload["severity"] = self.severity.value
        return payload


@dataclass(frozen=True)
class RuleResult:
    """
    Evaluation result for one standards rule.

    `evidence` contains only project facts used by the evaluator.
    """

    rule_id: str
    title: str
    category: str
    status: RuleStatus
    severity: RuleSeverity
    message: str
    requirement: str
    source: str
    section: str
    verification_source: str
    evidence: dict[str, Any]

    @property
    def passed(self) -> bool:
        """True only for an explicit PASS result."""
        return self.status is RuleStatus.PASS

    @property
    def blocking(self) -> bool:
        """
        Whether this result should currently block compliance.

        A warning is deliberately non-blocking.
        A NOT_EVALUATED mandatory rule is not treated as a pass.
        """
        return (
            self.severity is RuleSeverity.MANDATORY
            and self.status is RuleStatus.FAIL
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation for APIs/UI."""
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "category": self.category,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "requirement": self.requirement,
            "source": self.source,
            "section": self.section,
            "verification_source": self.verification_source,
            "evidence": self.evidence,
            "passed": self.passed,
            "blocking": self.blocking,
        }


@dataclass(frozen=True)
class ComplianceSummary:
    """Aggregate state of a standards evaluation."""

    total: int
    passed: int
    failed: int
    warnings: int
    not_evaluated: int
    blocking: int

    @property
    def compliant(self) -> bool:
        """
        A project is prescreen-compliant only when no mandatory rule fails
        and no mandatory rule remains unevaluated.

        This intentionally avoids declaring a project compliant when
        engineering verification is still missing.
        """
        return self.failed == 0 and self.not_evaluated == 0

    @property
    def score(self) -> float:
        """
        Conservative completion score.

        NOT_EVALUATED rules are not counted as passes.
        Warnings do not reduce the score because they are advisory.
        """
        if self.total == 0:
            return 0.0

        return round((self.passed / self.total) * 100, 2)


@dataclass(frozen=True)
class StandardsEvaluation:
    """Complete standards-engine output."""

    standard: str
    standard_version: str
    results: tuple[RuleResult, ...]
    summary: ComplianceSummary

    def to_dict(self) -> dict[str, Any]:
        """Return an API/frontend-friendly representation."""
        return {
            "standard": self.standard,
            "standard_version": self.standard_version,
            "results": [result.to_dict() for result in self.results],
            "summary": asdict(self.summary),
            "compliant": self.summary.compliant,
            "score": self.summary.score,
        }


# ---------------------------------------------------------------------------
# Sphere rule catalog
# ---------------------------------------------------------------------------


SPHERE_STANDARD_NAME = "Sphere Handbook"
SPHERE_STANDARD_VERSION = "V24.1"

SHELTER_STRUCTURAL_STABILITY_SECTION = (
    "Shelter standard 2: Structural Stability"
)

TECHNICAL_INDICATORS_SECTION = "Technical Indicators"


SPHERE_RULES: tuple[StandardRule, ...] = (
    StandardRule(
        rule_id="SPHERE-SHELTER-2.1",
        title="Assess structural hazards",
        category="structural_hazard",
        requirement=(
            "Identify and mitigate risks from natural hazards such as "
            "earthquakes, floods, and high winds during site selection "
            "and construction."
        ),
        source=(
            "Sphere Handbook V24.1 — Shelter standard 2: "
            "Structural Stability"
        ),
        section=SHELTER_STRUCTURAL_STABILITY_SECTION,
        severity=RuleSeverity.MANDATORY,
        verification_source="Site/environment assessment",
        description=(
            "Hazard conditions must be considered before structural "
            "prescreening can be treated as complete."
        ),
    ),
    StandardRule(
        rule_id="SPHERE-SHELTER-2.2",
        title="Use appropriate materials",
        category="materials",
        requirement=(
            "Select building materials and construction techniques that "
            "are culturally acceptable, climate-appropriate, and "
            "technically sound. Prioritize local materials where "
            "sustainable."
        ),
        source=(
            "Sphere Handbook V24.1 — Shelter standard 2: "
            "Structural Stability"
        ),
        section=SHELTER_STRUCTURAL_STABILITY_SECTION,
        severity=RuleSeverity.MANDATORY,
        verification_source="Material library / project BOM",
        description=(
            "The project must define materials before material suitability "
            "can be assessed."
        ),
    ),
    StandardRule(
        rule_id="SPHERE-TECH-WIND-001",
        title="Wind Load Resistance",
        category="wind",
        requirement="> 120 km/h sustained",
        source="Sphere Handbook V24.1 — Technical Indicators",
        section=TECHNICAL_INDICATORS_SECTION,
        severity=RuleSeverity.MANDATORY,
        verification_source="Engineering sign-off / field testing",
        description=(
            "Wind resistance requires structural analysis or field "
            "verification; material presence alone is insufficient."
        ),
    ),
    StandardRule(
        rule_id="SPHERE-TECH-SNOW-001",
        title="Snow Load Capacity",
        category="snow",
        requirement="> 50 kg/m²",
        source="Sphere Handbook V24.1 — Technical Indicators",
        section=TECHNICAL_INDICATORS_SECTION,
        severity=RuleSeverity.MANDATORY,
        verification_source="Visual inspection / rafter span calculations",
        description=(
            "Snow capacity requires a load-capacity calculation or "
            "appropriate verification evidence."
        ),
    ),
    StandardRule(
        rule_id="SPHERE-TECH-LIFE-001",
        title="Lifespan of Emergency Shelter",
        category="durability",
        requirement="Minimum 6 months",
        source="Sphere Handbook V24.1 — Technical Indicators",
        section=TECHNICAL_INDICATORS_SECTION,
        severity=RuleSeverity.MANDATORY,
        verification_source="Material procurement logs / post-distribution monitoring",
        description=(
            "Emergency shelter durability requires material or monitoring "
            "evidence."
        ),
    ),
    StandardRule(
        rule_id="SPHERE-STRUCT-BRACE-001",
        title="Cross-bracing",
        category="lateral_stability",
        requirement=(
            "Adequate cross-bracing in both wall planes is mandatory "
            "to resist lateral wind loads."
        ),
        source=(
            "Sphere Handbook V24.1 — Structural Stability guidance"
        ),
        section=SHELTER_STRUCTURAL_STABILITY_SECTION,
        severity=RuleSeverity.MANDATORY,
        verification_source="Structural calculation matrix",
        description=(
            "The current ConstraintSet does not yet model bracing geometry, "
            "so this remains unevaluated until structural analysis is added."
        ),
    ),
)


# Immutable lookup index.
_RULE_INDEX: Mapping[str, StandardRule] = {
    rule.rule_id: rule for rule in SPHERE_RULES
}


# ---------------------------------------------------------------------------
# Public catalog API
# ---------------------------------------------------------------------------


def get_sphere_rules() -> tuple[StandardRule, ...]:
    """Return the complete Panah Sphere rule catalog."""
    return SPHERE_RULES


def get_rule(rule_id: str) -> StandardRule:
    """
    Return a single rule by ID.

    Raises
    ------
    KeyError
        If the requested rule is not registered.
    """
    try:
        return _RULE_INDEX[rule_id]
    except KeyError as exc:
        raise KeyError(f"Unknown Panah rule: {rule_id}") from exc


def rules_by_category(category: str) -> tuple[StandardRule, ...]:
    """Return rules belonging to one category."""
    return tuple(rule for rule in SPHERE_RULES if rule.category == category)


def extract_sphere_rules() -> list[dict[str, Any]]:
    """
    Export the standards catalog in the structure expected by UI/API layers.

    This is the machine-readable representation of the standards presently
    represented in the Panah frontend's Sphere Handbook screen.
    """
    return [rule.to_dict() for rule in SPHERE_RULES]


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------


def _make_result(
    rule: StandardRule,
    status: RuleStatus,
    message: str,
    evidence: dict[str, Any] | None = None,
) -> RuleResult:
    """Create a consistent rule result."""
    return RuleResult(
        rule_id=rule.rule_id,
        title=rule.title,
        category=rule.category,
        status=status,
        severity=rule.severity,
        message=message,
        requirement=rule.requirement,
        source=rule.source,
        section=rule.section,
        verification_source=rule.verification_source,
        evidence=evidence or {},
    )


def _evaluate_hazard_rule(constraints: ConstraintSet) -> RuleResult:
    rule = get_rule("SPHERE-SHELTER-2.1")

    scenario = constraints.environment.scenario.strip()

    if scenario:
        return _make_result(
            rule,
            RuleStatus.PASS,
            "Environmental scenario supplied for structural hazard assessment.",
            {
                "environment_scenario": constraints.environment.scenario,
                "assessment_state": "scenario_supplied",
            },
        )

    return _make_result(
        rule,
        RuleStatus.NOT_EVALUATED,
        "No environmental scenario is available for hazard assessment.",
        {"assessment_state": "missing_environment_scenario"},
    )


def _evaluate_material_rule(constraints: ConstraintSet) -> RuleResult:
    rule = get_rule("SPHERE-SHELTER-2.2")

    if not constraints.materials:
        return _make_result(
            rule,
            RuleStatus.FAIL,
            "No project materials are defined.",
            {"material_count": 0},
        )

    return _make_result(
        rule,
        RuleStatus.PASS,
        "Project materials are defined and available for suitability analysis.",
        {
            "material_count": len(constraints.materials),
            "material_ids": [material.id for material in constraints.materials],
            "material_types": [material.type for material in constraints.materials],
        },
    )


def _evaluate_wind_rule(constraints: ConstraintSet) -> RuleResult:
    del constraints

    rule = get_rule("SPHERE-TECH-WIND-001")

    return _make_result(
        rule,
        RuleStatus.NOT_EVALUATED,
        (
            "Wind resistance requires structural analysis or field "
            "verification; the current ConstraintSet contains no wind "
            "capacity result."
        ),
        {
            "required_sustained_wind_kmh": 120,
            "comparison": "greater_than",
            "analysis_required": True,
        },
    )


def _evaluate_snow_rule(constraints: ConstraintSet) -> RuleResult:
    del constraints

    rule = get_rule("SPHERE-TECH-SNOW-001")

    return _make_result(
        rule,
        RuleStatus.NOT_EVALUATED,
        (
            "Snow-load capacity requires load-capacity evidence; the "
            "current ConstraintSet contains no snow-load result."
        ),
        {
            "required_snow_load_kg_m2": 50,
            "comparison": "greater_than",
            "analysis_required": True,
        },
    )


def _evaluate_lifespan_rule(constraints: ConstraintSet) -> RuleResult:
    del constraints

    rule = get_rule("SPHERE-TECH-LIFE-001")

    return _make_result(
        rule,
        RuleStatus.NOT_EVALUATED,
        (
            "Shelter lifespan requires material durability or monitoring "
            "evidence; the current ConstraintSet contains no lifespan result."
        ),
        {
            "minimum_lifespan_months": 6,
            "comparison": "greater_than_or_equal",
            "evidence_required": True,
        },
    )


def _evaluate_bracing_rule(constraints: ConstraintSet) -> RuleResult:
    del constraints

    rule = get_rule("SPHERE-STRUCT-BRACE-001")

    return _make_result(
        rule,
        RuleStatus.NOT_EVALUATED,
        (
            "Cross-bracing cannot yet be verified because the current "
            "ConstraintSet contains no bracing geometry or structural "
            "calculation matrix."
        ),
        {
            "required_wall_planes": 2,
            "analysis_required": True,
        },
    )


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------


def evaluate_structural_rules(
    constraints: ConstraintSet,
) -> list[RuleResult]:
    """
    Evaluate all currently supported structural prescreen rules.

    The order is intentionally stable because the frontend can present
    the resulting rule cards in standards-document order.
    """
    return [
        _evaluate_hazard_rule(constraints),
        _evaluate_material_rule(constraints),
        _evaluate_wind_rule(constraints),
        _evaluate_snow_rule(constraints),
        _evaluate_lifespan_rule(constraints),
        _evaluate_bracing_rule(constraints),
    ]


def summarize_results(
    results: list[RuleResult] | tuple[RuleResult, ...],
) -> ComplianceSummary:
    """Build an aggregate compliance summary."""
    passed = sum(result.status is RuleStatus.PASS for result in results)
    failed = sum(result.status is RuleStatus.FAIL for result in results)
    warnings = sum(result.status is RuleStatus.WARNING for result in results)
    not_evaluated = sum(
        result.status is RuleStatus.NOT_EVALUATED for result in results
    )
    blocking = sum(result.blocking for result in results)

    return ComplianceSummary(
        total=len(results),
        passed=passed,
        failed=failed,
        warnings=warnings,
        not_evaluated=not_evaluated,
        blocking=blocking,
    )


def evaluate_rules(constraints: ConstraintSet) -> StandardsEvaluation:
    """
    Public standards-engine entry point.

    Returns both individual rule results and an aggregate summary.
    """
    results = evaluate_structural_rules(constraints)
    summary = summarize_results(results)

    return StandardsEvaluation(
        standard=SPHERE_STANDARD_NAME,
        standard_version=SPHERE_STANDARD_VERSION,
        results=tuple(results),
        summary=summary,
    )


__all__ = [
    "ComplianceSummary",
    "RuleResult",
    "RuleSeverity",
    "RuleStatus",
    "SPHERE_RULES",
    "SPHERE_STANDARD_NAME",
    "SPHERE_STANDARD_VERSION",
    "StandardRule",
    "StandardsEvaluation",
    "evaluate_rules",
    "evaluate_structural_rules",
    "extract_sphere_rules",
    "get_rule",
    "get_sphere_rules",
    "rules_by_category",
    "summarize_results",
]