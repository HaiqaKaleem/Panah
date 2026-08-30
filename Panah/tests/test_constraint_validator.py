import pytest

from app.constraints.schemas import ConstraintSet
from app.constraints.validator import (
    ConstraintValidationError,
    inspect_constraint_set,
    validate_constraint_payload,
    validate_constraint_set,
)


def make_constraint_set(
    *,
    design_target: str = "roof_truss",
    materials: list[dict] | None = None,
    unknowns: list[str] | None = None,
) -> ConstraintSet:
    return ConstraintSet(
        version="CS-001",
        occupancy={
            "people": 6,
        },
        site={
            "length_m": 6,
            "width_m": 5,
        },
        materials=materials
        or [
            {
                "id": "MAT-01",
                "type": "bamboo",
                "qty": 24,
                "length_m": 6,
                "diameter_m": 0.06,
            }
        ],
        environment={
            "scenario": "configured_case",
        },
        design_target=design_target,
        unknowns=unknowns or [],
    )


def test_valid_constraint_set():
    report = inspect_constraint_set(
        make_constraint_set()
    )

    assert report.is_valid
    assert report.errors == ()


def test_duplicate_material_id_is_error():
    report = inspect_constraint_set(
        make_constraint_set(
            materials=[
                {
                    "id": "MAT-01",
                    "type": "bamboo",
                    "qty": 24,
                    "length_m": 6,
                },
                {
                    "id": "MAT-01",
                    "type": "steel",
                    "qty": 10,
                    "length_m": 6,
                },
            ]
        )
    )

    assert not report.is_valid
    assert report.errors[0].rule_id == "CS-D002"


def test_duplicate_unknown_is_error():
    report = inspect_constraint_set(
        make_constraint_set(
            unknowns=[
                "wind_exposure",
                "wind_exposure",
            ]
        )
    )

    assert not report.is_valid
    assert report.errors[0].rule_id == "CS-D004"


def test_blank_unknown_is_error():
    report = inspect_constraint_set(
        make_constraint_set(
            unknowns=[" "]
        )
    )

    assert not report.is_valid
    assert report.errors[0].rule_id == "CS-D003"


def test_unsupported_design_target_is_error():
    report = inspect_constraint_set(
        make_constraint_set(
            design_target="unsupported_target"
        )
    )

    assert not report.is_valid
    assert report.errors[0].rule_id == "CS-D001"


def test_orientation_issue_is_warning():
    report = inspect_constraint_set(
        ConstraintSet(
            version="CS-002",
            occupancy={"people": 6},
            site={
                "length_m": 4,
                "width_m": 6,
            },
            materials=[
                {
                    "id": "MAT-01",
                    "type": "bamboo",
                    "qty": 24,
                    "length_m": 6,
                }
            ],
            environment={
                "scenario": "configured_case",
            },
            design_target="roof_truss",
        )
    )

    assert report.is_valid
    assert any(
        warning.rule_id == "CS-W001"
        for warning in report.warnings
    )


def test_short_material_is_warning_not_error():
    report = inspect_constraint_set(
        make_constraint_set(
            materials=[
                {
                    "id": "MAT-01",
                    "type": "bamboo",
                    "qty": 24,
                    "length_m": 2,
                }
            ]
        )
    )

    assert report.is_valid

    assert any(
        warning.rule_id == "CS-W002"
        for warning in report.warnings
    )


def test_validate_raises_structured_error():
    with pytest.raises(
        ConstraintValidationError
    ) as exc_info:
        validate_constraint_set(
            make_constraint_set(
                design_target="unsupported_target"
            )
        )

    error = exc_info.value

    assert error.report.is_valid is False
    assert error.report.errors[0].rule_id == "CS-D001"


def test_payload_validation():
    constraint_set = make_constraint_set()

    result = validate_constraint_payload(
        constraint_set.model_dump()
    )

    assert result.version == "CS-001"
    assert result.design_target == "roof_truss"


def test_report_is_serializable():
    report = inspect_constraint_set(
        make_constraint_set(
            materials=[
                {
                    "id": "MAT-01",
                    "type": "bamboo",
                    "qty": 24,
                    "length_m": 2,
                }
            ]
        )
    )

    payload = report.as_dict()

    assert payload["valid"] is True
    assert payload["errors"] == []
    assert payload["warnings"][0]["rule_id"] == "CS-W002"


def test_validation_does_not_create_safety_verdict():
    report = inspect_constraint_set(
        make_constraint_set()
    )

    payload = report.as_dict()

    assert "safe" not in payload
    assert "approval" not in payload
    assert "safety_status" not in payload
    assert "engineering_approval" not in payload