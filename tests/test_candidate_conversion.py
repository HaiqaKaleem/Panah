from app.constraints.builder import build_constraint_set
from app.generator.converter import candidate_to_design_version
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


def test_candidate_becomes_canonical_design_version():
    candidate = LocalGenerationService().generate(
        constraints(),
        candidate_index=2,
    )

    design = candidate_to_design_version(
        candidate,
        version="DV-001",
    )

    assert design.schema_version == "1.0.0"
    assert design.version == "DV-001"
    assert design.design_type == "roof_truss"
    assert design.span_m == candidate.span_m
    assert design.height_m == candidate.height_m
    assert len(design.members) == len(candidate.members)
    assert len(design.connections) == len(candidate.connections)


def test_component_and_material_identity_survives_conversion():
    candidate = LocalGenerationService().generate(
        constraints(),
        candidate_index=2,
    )

    design = candidate_to_design_version(candidate, version="DV-002")

    assert [m.id for m in design.members] == [
        m.id for m in candidate.members
    ]
    assert [m.material_id for m in design.members] == [
        m.material_id for m in candidate.members
    ]


def test_connections_survive_conversion():
    candidate = LocalGenerationService().generate(constraints())

    design = candidate_to_design_version(candidate, version="DV-003")

    assert [
    (c.a, c.b, c.type)
    for c in design.connections
] == [
    (c.a, c.b, c.type)
    for c in candidate.connections
]


def test_conversion_does_not_modify_candidate():
    candidate = LocalGenerationService().generate(constraints())
    before = candidate.model_dump()

    candidate_to_design_version(candidate, version="DV-004")

    assert candidate.model_dump() == before
