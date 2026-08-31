import pytest

from app.constraints.builder import build_constraint_set
from app.generator.service import LocalGenerationService


def constraints():
    return build_constraint_set(
        version="CS-001",
        occupants=6,
        site_length_m=6.0,
        site_width_m=5.0,
        materials=[
            {
                "id": "MAT-01",
                "type": "bamboo",
                "qty": 24,
                "length_m": 4.5,
                "diameter_m": 0.06,
            }
        ],
        environment_scenario="configured_case",
        design_target="roof_truss",
    )


def test_generates_one_candidate_without_external_services():
    result = LocalGenerationService().generate(constraints())

    assert result.candidate_id == "LOCAL-01"
    assert result.generation_method == "local_constraint_generator"
    assert result.design_type == "roof_truss"
    assert len(result.members) >= 2


def test_generates_three_distinct_candidates():
    results = LocalGenerationService().generate_candidates(constraints(), count=3)

    assert len(results) == 3
    assert [r.candidate_id for r in results] == [
        "LOCAL-01",
        "LOCAL-02",
        "LOCAL-03",
    ]


def test_conservative_candidate_respects_available_member_length():
    result = LocalGenerationService().generate(
        constraints(),
        candidate_index=2,
    )

    assert result.span_m <= 4.5


def test_component_and_material_ids_are_preserved():
    result = LocalGenerationService().generate(constraints(), candidate_index=2)

    assert result.members[0].id == "M1"
    assert all(member.material_id == "MAT-01" for member in result.members)
    assert all(connection.a == "M1" for connection in result.connections)


def test_unsupported_target_rejected():
    data = constraints()
    data.design_target = "wall_panel"

    with pytest.raises(ValueError, match="Unsupported generation target"):
        LocalGenerationService().generate(data)


def test_invalid_candidate_count_rejected():
    with pytest.raises(ValueError, match="count must be between"):
        LocalGenerationService().generate_candidates(constraints(), count=4)


def test_invalid_candidate_index_rejected():
    with pytest.raises(ValueError, match="candidate_index"):
        LocalGenerationService().generate(constraints(), candidate_index=4)
