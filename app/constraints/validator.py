from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from app.constraints.schemas import ConstraintSet


Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class ConstraintDiagnostic:
    """
    One deterministic diagnostic produced by constraint validation.

    Diagnostics are deliberately separate from safety or engineering
    approval decisions.
    """

    rule_id: str
    severity: Severity
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ConstraintValidationReport:
    """
    Complete deterministic validation report for a ConstraintSet.
    """

    constraint_set: ConstraintSet
    diagnostics: tuple[ConstraintDiagnostic, ...]

    @property
    def errors(self) -> tuple[ConstraintDiagnostic, ...]:
        return tuple(
            diagnostic
            for diagnostic in self.diagnostics
            if diagnostic.severity == "error"
        )

    @property
    def warnings(self) -> tuple[ConstraintDiagnostic, ...]:
        return tuple(
            diagnostic
            for diagnostic in self.diagnostics
            if diagnostic.severity == "warning"
        )

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.is_valid,
            "errors": [
                diagnostic.as_dict()
                for diagnostic in self.errors
            ],
            "warnings": [
                diagnostic.as_dict()
                for diagnostic in self.warnings
            ],
        }


class ConstraintValidationError(ValueError):
    """
    Raised when a structurally valid ConstraintSet violates
    deterministic domain constraints.
    """

    def __init__(
        self,
        report: ConstraintValidationReport,
    ) -> None:
        self.report = report

        super().__init__(
            "ConstraintSet failed validation with "
            f"{len(report.errors)} error(s)."
        )


# This currently mirrors the generation capability already present
# in the repository. Adding another target later does not require
# changing the validation architecture.
SUPPORTED_DESIGN_TARGETS = frozenset(
    {
        "roof_truss",
    }
)


def inspect_constraint_set(
    value: ConstraintSet | Mapping[str, Any],
) -> ConstraintValidationReport:
    """
    Parse and inspect a ConstraintSet.

    Pydantic remains responsible for structural/schema validation.
    This layer performs deterministic cross-field/domain validation.

    Warnings do not invalidate the ConstraintSet.
    Errors do.
    """

    constraint_set = (
        value
        if isinstance(value, ConstraintSet)
        else ConstraintSet.model_validate(value)
    )

    diagnostics: list[ConstraintDiagnostic] = []

    _validate_design_target(
        constraint_set,
        diagnostics,
    )

    _validate_material_ids(
        constraint_set,
        diagnostics,
    )

    _validate_unknowns(
        constraint_set,
        diagnostics,
    )

    _validate_generation_feasibility_hints(
        constraint_set,
        diagnostics,
    )

    return ConstraintValidationReport(
        constraint_set=constraint_set,
        diagnostics=tuple(diagnostics),
    )


def validate_constraint_set(
    value: ConstraintSet | Mapping[str, Any],
) -> ConstraintSet:
    """
    Validate a ConstraintSet and return its normalized model.

    Raises ConstraintValidationError when deterministic domain
    errors are present.
    """

    report = inspect_constraint_set(value)

    if not report.is_valid:
        raise ConstraintValidationError(report)

    return report.constraint_set


def validate_constraint_payload(
    payload: Mapping[str, Any],
) -> ConstraintSet:
    """
    Explicit API-boundary helper for JSON-like payloads.
    """

    return validate_constraint_set(payload)


def _validate_design_target(
    constraint_set: ConstraintSet,
    diagnostics: list[ConstraintDiagnostic],
) -> None:
    if constraint_set.design_target not in SUPPORTED_DESIGN_TARGETS:
        diagnostics.append(
            ConstraintDiagnostic(
                rule_id="CS-D001",
                severity="error",
                path="design_target",
                message=(
                    "Unsupported design target: "
                    f"{constraint_set.design_target}"
                ),
            )
        )


def _validate_material_ids(
    constraint_set: ConstraintSet,
    diagnostics: list[ConstraintDiagnostic],
) -> None:
    seen: set[str] = set()

    for index, material in enumerate(
        constraint_set.materials
    ):
        if material.id in seen:
            diagnostics.append(
                ConstraintDiagnostic(
                    rule_id="CS-D002",
                    severity="error",
                    path=f"materials[{index}].id",
                    message=(
                        "Duplicate material id: "
                        f"{material.id}"
                    ),
                )
            )

        seen.add(material.id)


def _validate_unknowns(
    constraint_set: ConstraintSet,
    diagnostics: list[ConstraintDiagnostic],
) -> None:
    seen: set[str] = set()

    for index, unknown in enumerate(
        constraint_set.unknowns
    ):
        normalized = unknown.strip()

        if not normalized:
            diagnostics.append(
                ConstraintDiagnostic(
                    rule_id="CS-D003",
                    severity="error",
                    path=f"unknowns[{index}]",
                    message=(
                        "Unknown constraint identifier "
                        "cannot be blank."
                    ),
                )
            )
            continue

        if normalized in seen:
            diagnostics.append(
                ConstraintDiagnostic(
                    rule_id="CS-D004",
                    severity="error",
                    path=f"unknowns[{index}]",
                    message=(
                        "Duplicate unknown constraint: "
                        f"{normalized}"
                    ),
                )
            )

        seen.add(normalized)


def _validate_generation_feasibility_hints(
    constraint_set: ConstraintSet,
    diagnostics: list[ConstraintDiagnostic],
) -> None:
    """
    Produce non-blocking generation hints.

    These are NOT structural safety checks.

    They simply identify situations where the current deterministic
    generator may need segmentation, joining, or another strategy.
    """

    site_length = constraint_set.site.length_m

    if site_length < constraint_set.site.width_m:
        diagnostics.append(
            ConstraintDiagnostic(
                rule_id="CS-W001",
                severity="warning",
                path="site",
                message=(
                    "Site length is smaller than site width; "
                    "verify orientation before generation."
                ),
            )
        )

    if not any(
        material.length_m >= site_length
        for material in constraint_set.materials
    ):
        diagnostics.append(
            ConstraintDiagnostic(
                rule_id="CS-W002",
                severity="warning",
                path="materials",
                message=(
                    "No available material piece reaches the "
                    "declared site length; generation may require "
                    "segmentation or joining."
                ),
            )
        )