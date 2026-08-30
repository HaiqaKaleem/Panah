
import pytest

from app.geometry.builder import build_geometry
from app.geometry.primitives import member_to_primitive
from app.schemas.design_version import CanonicalDesignVersion, DesignMember


def member(
    member_id="M1",
    member_type="beam",
    length=4.2,
    diameter=0.06,
):
    return DesignMember(
        id=member_id,
        type=member_type,
        material_id="MAT-01",
        length_m=length,
        diameter_m=diameter,
    )


def design(*members):
    return CanonicalDesignVersion(
        schema_version="1.0.0",
        design_type="roof_truss",
        version="DV-001",
        span_m=4.2,
        height_m=1.0,
        members=list(members),
        connections=[],
        metadata={
            "generator_name": "test-generator",
            "generator_version": "1.0",
        },
    )


def test_beam_conversion():
    result = member_to_primitive(member())

    assert result.component_id == "M1"
    assert result.geometry_type == "beam"
    assert result.material_id == "MAT-01"
    assert result.dimensions.length_m == 4.2
    assert result.dimensions.width_m == 0.06


def test_brace_conversion():
    result = member_to_primitive(
        member("M2", "brace", 2.3)
    )

    assert result.component_id == "M2"
    assert result.geometry_type == "brace"
    assert result.dimensions.length_m == 2.3


def test_builder_converts_all_members():
    result = build_geometry(
        design(
            member("M1"),
            member("M2", "brace", 2.3),
        )
    )

    assert len(result.primitives) == 2
    assert [p.component_id for p in result.primitives] == ["M1", "M2"]


def test_material_ids_are_preserved():
    result = build_geometry(design(member("M1")))

    assert result.primitives[0].material_id == "MAT-01"


def test_design_version_is_preserved():
    result = build_geometry(design(member("M1")))

    assert result.design_version_id == "DV-001"


def test_unsupported_member_type_fails():
    with pytest.raises(ValueError, match="Unsupported geometry member type"):
        member_to_primitive(
            member("M1", "column")
        )


def test_missing_diameter_fails():
    m = member("M1")
    m.diameter_m = None

    with pytest.raises(ValueError, match="requires diameter_m"):
        member_to_primitive(m)


def test_unsupported_design_type_fails():
    d = design(member("M1"))
    d.design_type = "complete_house"

    with pytest.raises(ValueError, match="Unsupported design type"):
        build_geometry(d)


def test_output_is_not_mesh_data():
    primitive = build_geometry(
        design(member("M1"))
    ).primitives[0]

    assert not hasattr(primitive, "vertices")
    assert not hasattr(primitive, "faces")