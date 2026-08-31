import pytest
from pydantic import ValidationError

from app.schemas.design_version import CanonicalDesignVersion


def valid_design():
    return {
        "schema_version": "1.0.0",
        "design_type": "roof_truss",
        "version": "DV-001",
        "span_m": 4.2,
        "height_m": 1.0,
        "members": [
            {
                "id": "M1",
                "type": "beam",
                "material_id": "MAT-01",
                "length_m": 4.2,
            },
            {
                "id": "M2",
                "type": "brace",
                "material_id": "MAT-01",
                "length_m": 2.3,
            },
        ],
        "connections": [
            {"id": "C1", "a": "M1", "b": "M2", "type": "bolted"}
        ],
        "metadata": {
            "generator_name": "mock-parametric-generator",
            "generator_version": "1.0",
            "source_constraint_set_id": "CS-001",
        },
    }


def test_valid_design_version():
    design = CanonicalDesignVersion.model_validate(valid_design())

    assert design.design_type == "roof_truss"
    assert len(design.members) == 2
    assert design.connections[0].a == "M1"


def test_rejects_unknown_connection_member():
    payload = valid_design()
    payload["connections"][0]["b"] = "M99"

    with pytest.raises(ValidationError, match="unknown member"):
        CanonicalDesignVersion.model_validate(payload)


def test_rejects_duplicate_member_ids():
    payload = valid_design()
    payload["members"][1]["id"] = "M1"

    with pytest.raises(ValidationError, match="member IDs must be unique"):
        CanonicalDesignVersion.model_validate(payload)


def test_rejects_duplicate_connection_ids():
    payload = valid_design()
    payload["connections"].append(
        {"id": "C1", "a": "M1", "b": "M2", "type": "bolted"}
    )

    with pytest.raises(ValidationError, match="connection IDs must be unique"):
        CanonicalDesignVersion.model_validate(payload)


def test_rejects_unknown_fields():
    payload = valid_design()
    payload["safe"] = True

    with pytest.raises(ValidationError):
        CanonicalDesignVersion.model_validate(payload)


def test_rejects_invalid_schema_version():
    payload = valid_design()
    payload["schema_version"] = "v1"

    with pytest.raises(ValidationError, match="semantic version"):
        CanonicalDesignVersion.model_validate(payload)


def test_rejects_self_connection():
    payload = valid_design()
    payload["connections"][0]["b"] = "M1"

    with pytest.raises(ValidationError, match="endpoints must be different"):
        CanonicalDesignVersion.model_validate(payload)


def test_design_has_no_validation_verdict():
    design = CanonicalDesignVersion.model_validate(valid_design())
    dumped = design.model_dump()

    assert "status" not in dumped
    assert "validation_status" not in dumped
    assert "safe" not in dumped
    assert "approval" not in dumped
