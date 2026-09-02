
import pytest

from app.geometry.builder import build_geometry
from app.geometry.primitives import member_to_primitive
from app.schemas.design_version import (
    CanonicalDesignVersion,
    DesignMember,
)


def make_member(
    member_id="M1",
    member_type="beam",
    length=4.2,
):
    return DesignMember(
        id=member_id,
        type=member_type,
        material_id="MAT-01",
        length_m=length,
        diameter_m=0.06,
    )


def make_design():
    return CanonicalDesignVersion(
        schema_version="1.0.0",
        design_type="roof_truss",
        version="DV-001",
        span_m=4.2,
        height_m=1.0,
        members=[
            make_member("M1", "beam", 4.2),
            make_member("M2", "brace", 2.3),
        ],
        connections=[],
        metadata={
            "generator_name": "test-generator",
            "generator_version": "1.0",
        },
    )


def test_beam_becomes_geometry_primitive():
    primitive = member_to_primitive(make_member())

    assert primitive.component_id == "M1"
    assert primitive.geometry_type == "beam"
    assert primitive.material_id == "MAT-01"
    assert primitive.dimensions.length_m == 4.2


def test_brace_becomes_geometry_primitive():
    primitive = member_to_primitive(
        make_member("M2", "brace", 2.3)
    )

    assert primitive.component_id == "M2"
    assert primitive.geometry_type == "brace"
    assert primitive.dimensions.length_m == 2.3


def test_builder_preserves_component_ids():
    result = build_geometry(make_design())

    assert [p.component_id for p in result.primitives] == [
        "M1",
        "M2",
    ]


def test_builder_preserves_material_ids():
    result = build_geometry(make_design())

    assert all(
        p.material_id == "MAT-01"
        for p in result.primitives
    )


def test_builder_preserves_design_version_id():
    result = build_geometry(make_design())

    assert result.design_version_id == "DV-001"


def test_unsupported_member_type_is_rejected():
    member = make_member()
    member.type = "column"

    with pytest.raises(ValueError, match="Unsupported geometry"):
        member_to_primitive(member)


def test_unsupported_design_type_is_rejected():
    design = make_design()
    design.design_type = "complete_house"

    with pytest.raises(ValueError, match="Unsupported design type"):
        build_geometry(design)


def test_geometry_output_is_structured_not_mesh_data():
    result = build_geometry(make_design())

    assert result.primitives[0].geometry_type == "beam"
    assert not hasattr(result.primitives[0], "vertices")
    assert not hasattr(result.primitives[0], "faces")