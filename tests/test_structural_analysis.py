from app.constraints.schemas import (
    ConstraintSet,
    EnvironmentConstraint,
    MaterialConstraint,
    OccupancyConstraint,
    SiteConstraint,
)
from app.rules import RuleStatus, evaluate_rules
from app.schemas.design_version import DesignMember
from app.structural.analysis import analyze_structure


def _constraints() -> ConstraintSet:
    return ConstraintSet(
        version="CS-001",
        occupancy=OccupancyConstraint(people=6),
        site=SiteConstraint(length_m=6, width_m=5),
        materials=[
            MaterialConstraint(
                id="MAT-BAM-01",
                type="treated_bamboo",
                qty=120,
                length_m=3,
                diameter_m=0.12,
            ),
        ],
        environment=EnvironmentConstraint(scenario="monsoon_lowland"),
        design_target="roof_truss",
    )


def _ridge_beam() -> DesignMember:
    return DesignMember(
        id="M-RIDGE-01",
        type="beam",
        material_id="MAT-BAM-01",
        length_m=4.2,
        diameter_m=0.12,
    )


def test_no_load_bearing_member_is_not_analyzable():
    result = analyze_structure(_constraints(), members=[])
    assert result.analyzable is False


def test_beam_without_bracing_is_analyzable_and_reports_no_bracing():
    result = analyze_structure(_constraints(), members=[_ridge_beam()])

    assert result.analyzable is True
    assert result.bracing_present is False
    assert result.dead_load_kg > 0
    assert result.max_deflection_mm is not None
    assert result.live_load_capacity_kg_m2 is not None


def test_unbraced_design_fails_wind_and_bracing_rules_end_to_end():
    """Mirrors the Figma demo scenario: a ridge beam spanning further than
    its material supports, with no cross-bracing -> wind shear should FAIL.
    """
    constraints = _constraints()
    analysis = analyze_structure(constraints, members=[_ridge_beam()])

    evaluation = evaluate_rules(constraints, analysis)
    results_by_id = {r.rule_id: r for r in evaluation.results}

    assert results_by_id["SPHERE-STRUCT-BRACE-001"].status == RuleStatus.FAIL
    assert results_by_id["SPHERE-TECH-WIND-001"].status == RuleStatus.FAIL
    # No longer NOT_EVALUATED now that analysis evidence exists.
    assert results_by_id["SPHERE-TECH-SNOW-001"].status in (
        RuleStatus.PASS,
        RuleStatus.FAIL,
    )
    assert results_by_id["SPHERE-TECH-LIFE-001"].status == RuleStatus.PASS


def test_adding_adequate_bracing_passes_wind_and_bracing_rules():
    constraints = _constraints()
    members = [
        _ridge_beam(),
        DesignMember(
            id="M-BRACE-01",
            type="brace",
            material_id="MAT-BAM-01",
            length_m=2.0,
            diameter_m=0.12,
        ),
        DesignMember(
            id="M-BRACE-02",
            type="brace",
            material_id="MAT-BAM-01",
            length_m=2.0,
            diameter_m=0.12,
        ),
        DesignMember(
            id="M-BRACE-03",
            type="brace",
            material_id="MAT-BAM-01",
            length_m=2.0,
            diameter_m=0.12,
        ),
        DesignMember(
            id="M-BRACE-04",
            type="brace",
            material_id="MAT-BAM-01",
            length_m=2.0,
            diameter_m=0.12,
        ),
    ]

    analysis = analyze_structure(constraints, members=members)
    evaluation = evaluate_rules(constraints, analysis)
    results_by_id = {r.rule_id: r for r in evaluation.results}

    assert analysis.bracing_present is True
    assert results_by_id["SPHERE-STRUCT-BRACE-001"].status == RuleStatus.PASS
    assert results_by_id["SPHERE-TECH-WIND-001"].status == RuleStatus.PASS


def test_without_analysis_rules_remain_not_evaluated_backward_compatible():
    constraints = _constraints()
    evaluation = evaluate_rules(constraints)
    results_by_id = {r.rule_id: r for r in evaluation.results}

    assert results_by_id["SPHERE-TECH-WIND-001"].status == RuleStatus.NOT_EVALUATED
    assert results_by_id["SPHERE-TECH-SNOW-001"].status == RuleStatus.NOT_EVALUATED
    assert results_by_id["SPHERE-TECH-LIFE-001"].status == RuleStatus.NOT_EVALUATED
    assert results_by_id["SPHERE-STRUCT-BRACE-001"].status == RuleStatus.NOT_EVALUATED
