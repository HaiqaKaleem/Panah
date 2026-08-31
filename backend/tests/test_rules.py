
from app.constraints.schemas import (
    ConstraintSet,
    EnvironmentConstraint,
    MaterialConstraint,
    OccupancyConstraint,
    SiteConstraint,
)
from app.rules import (
    RuleSeverity,
    RuleStatus,
    SPHERE_STANDARD_NAME,
    SPHERE_STANDARD_VERSION,
    evaluate_rules,
    evaluate_structural_rules,
    extract_sphere_rules,
    get_rule,
    get_sphere_rules,
    rules_by_category,
    summarize_results,
)


def valid_constraints() -> ConstraintSet:
    return ConstraintSet(
        version="CS-001",
        occupancy=OccupancyConstraint(people=6),
        site=SiteConstraint(
            length_m=6,
            width_m=5,
        ),
        materials=[
            MaterialConstraint(
                id="MAT-BAM-01",
                type="treated_bamboo",
                qty=120,
                length_m=3,
                diameter_m=0.12,
            )
        ],
        environment=EnvironmentConstraint(
            scenario="configured_site",
        ),
        design_target="roof_truss",
    )


# ---------------------------------------------------------------------------
# Catalog tests
# ---------------------------------------------------------------------------


def test_sphere_catalog_is_non_empty():
    rules = get_sphere_rules()

    assert rules
    assert len(rules) == 6


def test_sphere_catalog_has_unique_rule_ids():
    rules = get_sphere_rules()

    rule_ids = [rule.rule_id for rule in rules]

    assert len(rule_ids) == len(set(rule_ids))


def test_required_sphere_rules_exist():
    expected_ids = {
        "SPHERE-SHELTER-2.1",
        "SPHERE-SHELTER-2.2",
        "SPHERE-TECH-WIND-001",
        "SPHERE-TECH-SNOW-001",
        "SPHERE-TECH-LIFE-001",
        "SPHERE-STRUCT-BRACE-001",
    }

    actual_ids = {
        rule.rule_id
        for rule in get_sphere_rules()
    }

    assert actual_ids == expected_ids


def test_rule_lookup_returns_correct_rule():
    rule = get_rule("SPHERE-TECH-WIND-001")

    assert rule.title == "Wind Load Resistance"
    assert rule.category == "wind"
    assert rule.requirement == "> 120 km/h sustained"


def test_unknown_rule_id_raises_key_error():
    try:
        get_rule("DOES-NOT-EXIST")
    except KeyError as exc:
        assert "Unknown Panah rule" in str(exc)
    else:
        raise AssertionError("Expected KeyError for unknown rule ID")


def test_rules_can_be_filtered_by_category():
    wind_rules = rules_by_category("wind")

    assert len(wind_rules) == 1
    assert wind_rules[0].rule_id == "SPHERE-TECH-WIND-001"


# ---------------------------------------------------------------------------
# Standards extraction tests
# ---------------------------------------------------------------------------


def test_extract_sphere_rules_returns_serializable_records():
    extracted = extract_sphere_rules()

    assert isinstance(extracted, list)
    assert len(extracted) == 6

    for rule in extracted:
        assert isinstance(rule, dict)
        assert rule["rule_id"]
        assert rule["title"]
        assert rule["requirement"]
        assert rule["source"]
        assert rule["section"]
        assert rule["severity"]


def test_extracted_rules_preserve_sphere_provenance():
    extracted = extract_sphere_rules()

    sources = {
        rule["source"]
        for rule in extracted
    }

    assert any("Sphere Handbook V24.1" in source for source in sources)


# ---------------------------------------------------------------------------
# Individual rule evaluation
# ---------------------------------------------------------------------------


def test_structural_rules_return_results_for_every_catalog_rule():
    constraints = valid_constraints()

    results = evaluate_structural_rules(constraints)

    assert len(results) == len(get_sphere_rules())

    result_ids = {
        result.rule_id
        for result in results
    }

    catalog_ids = {
        rule.rule_id
        for rule in get_sphere_rules()
    }

    assert result_ids == catalog_ids


def test_hazard_rule_passes_when_environment_is_supplied():
    results = evaluate_structural_rules(valid_constraints())

    hazard = next(
        result
        for result in results
        if result.rule_id == "SPHERE-SHELTER-2.1"
    )

    assert hazard.status is RuleStatus.PASS
    assert hazard.evidence["environment_scenario"] == "configured_site"


def test_material_rule_passes_when_materials_are_supplied():
    results = evaluate_structural_rules(valid_constraints())

    material = next(
        result
        for result in results
        if result.rule_id == "SPHERE-SHELTER-2.2"
    )

    assert material.status is RuleStatus.PASS
    assert material.evidence["material_count"] == 1
    assert material.evidence["material_ids"] == ["MAT-BAM-01"]


def test_wind_rule_requires_structural_analysis():
    results = evaluate_structural_rules(valid_constraints())

    wind = next(
        result
        for result in results
        if result.rule_id == "SPHERE-TECH-WIND-001"
    )

    assert wind.status is RuleStatus.NOT_EVALUATED
    assert wind.evidence["required_sustained_wind_kmh"] == 120
    assert wind.evidence["comparison"] == "greater_than"
    assert wind.evidence["analysis_required"] is True


def test_snow_rule_requires_structural_analysis():
    results = evaluate_structural_rules(valid_constraints())

    snow = next(
        result
        for result in results
        if result.rule_id == "SPHERE-TECH-SNOW-001"
    )

    assert snow.status is RuleStatus.NOT_EVALUATED
    assert snow.evidence["required_snow_load_kg_m2"] == 50
    assert snow.evidence["comparison"] == "greater_than"


def test_lifespan_rule_requires_durability_evidence():
    results = evaluate_structural_rules(valid_constraints())

    lifespan = next(
        result
        for result in results
        if result.rule_id == "SPHERE-TECH-LIFE-001"
    )

    assert lifespan.status is RuleStatus.NOT_EVALUATED
    assert lifespan.evidence["minimum_lifespan_months"] == 6
    assert lifespan.evidence["comparison"] == "greater_than_or_equal"


def test_cross_bracing_rule_requires_geometry():
    results = evaluate_structural_rules(valid_constraints())

    bracing = next(
        result
        for result in results
        if result.rule_id == "SPHERE-STRUCT-BRACE-001"
    )

    assert bracing.status is RuleStatus.NOT_EVALUATED
    assert bracing.evidence["required_wall_planes"] == 2
    assert bracing.evidence["analysis_required"] is True


# ---------------------------------------------------------------------------
# Missing-input behavior
# ---------------------------------------------------------------------------


def test_missing_environment_does_not_fake_a_pass():
    constraints = valid_constraints()

    constraints = ConstraintSet(
        version=constraints.version,
        occupancy=constraints.occupancy,
        site=constraints.site,
        materials=constraints.materials,
        environment=EnvironmentConstraint(
            scenario=" ",
        ),
        design_target=constraints.design_target,
        unknowns=constraints.unknowns,
    )

    results = evaluate_structural_rules(constraints)

    hazard = next(
        result
        for result in results
        if result.rule_id == "SPHERE-SHELTER-2.1"
    )

    assert hazard.status is RuleStatus.NOT_EVALUATED

def test_constraint_set_rejects_missing_materials():
    from pydantic import ValidationError

    try:
        ConstraintSet(
            version="CS-002",
            occupancy=OccupancyConstraint(people=6),
            site=SiteConstraint(
                length_m=6,
                width_m=5,
            ),
            materials=[],
            environment=EnvironmentConstraint(
                scenario="configured_site",
            ),
            design_target="roof_truss",
        )
    except ValidationError as exc:
        assert "materials" in str(exc)
    else:
        raise AssertionError(
            "ConstraintSet must reject an empty materials list"
        )


# ---------------------------------------------------------------------------
# Aggregate evaluation
# ---------------------------------------------------------------------------


def test_evaluate_rules_returns_complete_standards_evaluation():
    evaluation = evaluate_rules(valid_constraints())

    assert evaluation.standard == SPHERE_STANDARD_NAME
    assert evaluation.standard_version == SPHERE_STANDARD_VERSION

    assert len(evaluation.results) == 6
    assert evaluation.summary.total == 6


def test_summary_counts_are_correct():
    evaluation = evaluate_rules(valid_constraints())

    summary = evaluation.summary

    assert summary.total == 6
    assert summary.passed == 2
    assert summary.failed == 0
    assert summary.warnings == 0
    assert summary.not_evaluated == 4
    assert summary.blocking == 0


def test_summary_is_not_compliant_when_mandatory_rules_are_unevaluated():
    evaluation = evaluate_rules(valid_constraints())

    assert evaluation.summary.compliant is False


def test_score_does_not_treat_unevaluated_rules_as_passes():
    evaluation = evaluate_rules(valid_constraints())

    assert evaluation.summary.score == 33.33


def test_rule_result_to_dict_contains_frontend_fields():
    evaluation = evaluate_rules(valid_constraints())

    wind = next(
        result
        for result in evaluation.results
        if result.rule_id == "SPHERE-TECH-WIND-001"
    )

    payload = wind.to_dict()

    assert payload["rule_id"] == "SPHERE-TECH-WIND-001"
    assert payload["status"] == "not_evaluated"
    assert payload["severity"] == RuleSeverity.MANDATORY.value
    assert payload["requirement"] == "> 120 km/h sustained"
    assert "Sphere Handbook V24.1" in payload["source"]
    assert payload["evidence"]["required_sustained_wind_kmh"] == 120
    assert payload["passed"] is False
    assert payload["blocking"] is False


def test_standards_evaluation_to_dict_is_frontend_ready():
    evaluation = evaluate_rules(valid_constraints())

    payload = evaluation.to_dict()

    assert payload["standard"] == "Sphere Handbook"
    assert payload["standard_version"] == "V24.1"
    assert len(payload["results"]) == 6
    assert payload["summary"]["total"] == 6
    assert payload["compliant"] is False
    assert payload["score"] == 33.33


# ---------------------------------------------------------------------------
# Summary helper
# ---------------------------------------------------------------------------


def test_summarize_results_handles_empty_input():
    summary = summarize_results([])

    assert summary.total == 0
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.warnings == 0
    assert summary.not_evaluated == 0
    assert summary.blocking == 0
    assert summary.compliant is True
    assert summary.score == 0.0