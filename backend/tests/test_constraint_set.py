import pytest
from pydantic import ValidationError
from app.constraints.builder import build_constraint_set
from app.constraints.schemas import ConstraintSet

def material():
    return {"id":"MAT-01","type":"bamboo","qty":24,"length_m":4.5,"diameter_m":0.06}

def test_blueprint_shape():
    r = build_constraint_set(version="CS-001", occupants=6, site_length_m=6, site_width_m=5,
                             materials=[material()], environment_scenario="configured_case")
    assert isinstance(r, ConstraintSet)
    assert r.schema_version == "1.0.0"
    assert r.occupancy.people == 6
    assert r.site.length_m == 6
    assert r.materials[0].id == "MAT-01"
    assert r.design_target == "roof_truss"
    assert r.unknowns == []

def test_unknowns_preserved():
    r = build_constraint_set(version="CS-002", occupants=6, site_length_m=6, site_width_m=5,
                             materials=[material()], environment_scenario="configured_case",
                             unknowns=["wind_exposure"])
    assert r.unknowns == ["wind_exposure"]

@pytest.mark.parametrize("field", ["occupants","site_length_m","site_width_m"])
def test_positive_constraints(field):
    args = dict(version="CS-003", occupants=6, site_length_m=6, site_width_m=5,
                materials=[material()], environment_scenario="configured_case")
    args[field] = 0
    with pytest.raises(ValidationError): build_constraint_set(**args)

def test_empty_materials_rejected():
    with pytest.raises(ValidationError):
        build_constraint_set(version="CS-004", occupants=6, site_length_m=6, site_width_m=5,
                             materials=[], environment_scenario="configured_case")

def test_extra_material_field_rejected():
    m = material(); m["unexpected"] = "x"
    with pytest.raises(ValidationError):
        build_constraint_set(version="CS-005", occupants=6, site_length_m=6, site_width_m=5,
                             materials=[m], environment_scenario="configured_case")

def test_payload_is_serializable():
    r = build_constraint_set(version="CS-006", occupants=6, site_length_m=6, site_width_m=5,
                             materials=[material()], environment_scenario="configured_case")
    p = r.model_dump()
    assert p["occupancy"] == {"people": 6}
    assert p["site"] == {"length_m": 6.0, "width_m": 5.0}
    assert p["materials"][0]["id"] == "MAT-01"
