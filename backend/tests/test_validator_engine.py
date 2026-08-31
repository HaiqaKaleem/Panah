"""
Golden test cases for the deterministic YAML validation engine.

Tests every rule type: geometry, material, load path, environment, connections.
"""
import pytest
from app.constraints.schemas import (
    ConstraintSet,
    EnvironmentConstraint,
    MaterialConstraint,
    OccupancyConstraint,
    SiteConstraint,
)
from app.schemas.design_version import (
    CanonicalDesignVersion,
    DesignConnection,
    DesignDimensions,
    DesignMember,
    DesignMetadata,
)
from app.validator import validate_design, build_context, list_rules, reload_rules
from app.validator.engine import ValidationEngine
from app.validator.result import ValidationReport, RuleResult, Severity


# ──────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────

def _make_design(
    span=5.0,
    height=2.5,
    width=4.0,
    members=None,
    connections=None,
):
    """Create a minimal valid CanonicalDesignVersion."""
    if members is None:
        members = [
            DesignMember(id="m1", type="beam", material_id="bamboo", length_m=span),
            DesignMember(id="m2", type="column", material_id="bamboo", length_m=height),
        ]
    if connections is None:
        connections = [
            DesignConnection(id="c1", a="m1", b="m2", type="bolted"),
        ]
    return CanonicalDesignVersion(
        design_type="roof_truss",
        span_m=span,
        height_m=height,
        footprint=DesignDimensions(length_m=span, width_m=width, height_m=height),
        members=members,
        connections=connections,
        metadata=DesignMetadata(
            generator_name="test",
            generator_version="0.1.0",
        ),
    )


def _make_constraints(
    site_length=6.0,
    site_width=5.0,
    material_type="treated_bamboo",
    material_qty=30.0,
    scenario="semi_arid_moderate_wind",
):
    """Create a minimal valid ConstraintSet."""
    return ConstraintSet(
        version="1.0.0",
        occupancy=OccupancyConstraint(people=5),
        site=SiteConstraint(length_m=site_length, width_m=site_width),
        materials=[
            MaterialConstraint(id="bamboo", type=material_type, qty=material_qty, length_m=6.0),
        ],
        environment=EnvironmentConstraint(scenario=scenario),
        design_target="emergency_shelter",
    )


# ──────────────────────────────────────────────────────────────────
# Rule discovery
# ──────────────────────────────────────────────────────────────────

class TestRuleDiscovery:
    def test_all_rules_loaded(self):
        rules = list_rules()
        assert len(rules) >= 8, f"Expected at least 8 rules, got {len(rules)}: {rules}"

    def test_expected_rule_ids_present(self):
        rules = list_rules()
        expected = ["R-GEO-001", "R-GEO-002", "R-GEO-003", "R-MAT-001", "R-MAT-002",
                     "R-LOAD-001", "R-ENV-001", "R-CONN-001"]
        for rule_id in expected:
            assert rule_id in rules, f"Missing rule: {rule_id}"

    def test_rules_can_be_reloaded(self):
        reload_rules()
        rules = list_rules()
        assert len(rules) >= 8


# ──────────────────────────────────────────────────────────────────
# R-GEO-001: Span ≤ site length
# ──────────────────────────────────────────────────────────────────

class TestRGeo001SpanConstraint:
    def test_pass_when_span_fits(self):
        design = _make_design(span=5.0)
        constraints = _make_constraints(site_length=6.0)
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-GEO-001"])
        assert report.passed_count == 1
        assert report.failed_count == 0
        assert report.results[0].passed

    def test_fail_when_span_exceeds_site(self):
        design = _make_design(span=7.0)
        constraints = _make_constraints(site_length=6.0)
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-GEO-001"])
        assert report.failed_count == 1
        assert report.results[0].status == "fail"
        assert "exceeds" in report.results[0].message.lower()

    def test_pass_when_span_equals_site(self):
        design = _make_design(span=6.0)
        constraints = _make_constraints(site_length=6.0)
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-GEO-001"])
        assert report.passed_count == 1


# ──────────────────────────────────────────────────────────────────
# R-GEO-002: Member length ≤ material stock
# ──────────────────────────────────────────────────────────────────

class TestRGeo002MemberLength:
    def test_pass_when_within_stock(self):
        design = _make_design(span=4.0)
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-GEO-002"])
        assert report.passed_count == 1

    def test_fail_when_exceeds_stock(self):
        design = _make_design(span=7.0)
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-GEO-002"])
        assert report.failed_count == 1


# ──────────────────────────────────────────────────────────────────
# R-GEO-003: Minimum clearance ≥ 2.0m
# ──────────────────────────────────────────────────────────────────

class TestRGeo003Clearance:
    def test_pass_when_height_adequate(self):
        design = _make_design(height=2.5)
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-GEO-003"])
        assert report.passed_count == 1

    def test_fail_when_too_short(self):
        design = _make_design(height=1.8)
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-GEO-003"])
        assert report.failed_count == 1

    def test_pass_when_exactly_2m(self):
        design = _make_design(height=2.0)
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-GEO-003"])
        assert report.passed_count == 1


# ──────────────────────────────────────────────────────────────────
# R-MAT-001: Materials list not empty
# ──────────────────────────────────────────────────────────────────

class TestRMat001MaterialsExist:
    def test_pass_with_materials(self):
        design = _make_design()
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-MAT-001"])
        assert report.passed_count == 1


# ──────────────────────────────────────────────────────────────────
# R-MAT-002: Material properties in catalog
# ──────────────────────────────────────────────────────────────────

class TestRMat002PropertiesExist:
    def test_pass_with_known_material(self):
        design = _make_design()
        constraints = _make_constraints(material_type="treated_bamboo")
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-MAT-002"])
        assert report.passed_count == 1

    def test_fail_with_unknown_material(self):
        design = _make_design()
        constraints = _make_constraints(material_type="unobtainium")
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-MAT-002"])
        assert report.failed_count == 1


# ──────────────────────────────────────────────────────────────────
# R-LOAD-001: Load path connectivity
# ──────────────────────────────────────────────────────────────────

class TestRLoad001Connectivity:
    def test_pass_with_connections(self):
        design = _make_design()
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-LOAD-001"])
        assert report.passed_count == 1

    def test_fail_without_connections(self):
        design = _make_design(connections=[])
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-LOAD-001"])
        assert report.failed_count == 1


# ──────────────────────────────────────────────────────────────────
# R-ENV-001: Environment scenario defined
# ──────────────────────────────────────────────────────────────────

class TestREnv001ScenarioDefined:
    def test_pass_with_scenario(self):
        design = _make_design()
        constraints = _make_constraints(scenario="semi_arid_moderate_wind")
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-ENV-001"])
        assert report.passed_count == 1

    def test_rule_idempotent_with_schema(self):
        # EnvironmentConstraint.scenario has min_length=1 in Pydantic, so empty
        # strings are rejected at the schema level. The R-ENV-001 rule acts as
        # a second line of defense if someone constructs a context manually.
        rules = list_rules()
        assert "R-ENV-001" in rules


# ──────────────────────────────────────────────────────────────────
# R-CONN-001: Connections defined
# ──────────────────────────────────────────────────────────────────

class TestRConn001ConnectionsDefined:
    def test_pass_with_connections(self):
        design = _make_design()
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-CONN-001"])
        assert report.passed_count == 1

    def test_fail_without_connections(self):
        design = _make_design(connections=[])
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx, rule_ids=["R-CONN-001"])
        assert report.failed_count == 1


# ──────────────────────────────────────────────────────────────────
# Full pipeline (all rules at once)
# ──────────────────────────────────────────────────────────────────

class TestFullPipeline:
    def test_all_pass_for_valid_design(self):
        design = _make_design(span=5.0, height=2.5)
        constraints = _make_constraints(site_length=6.0, material_type="treated_bamboo", scenario="semi_arid_moderate_wind")
        ctx = build_context(design, constraints)
        report = validate_design(ctx)
        assert report.overall_status == "pass"
        assert report.failed_count == 0
        assert report.passed_count >= 8

    def test_overall_fail_when_critical_rule_fails(self):
        design = _make_design(span=7.0, height=2.5)  # span exceeds site
        constraints = _make_constraints(site_length=6.0)
        ctx = build_context(design, constraints)
        report = validate_design(ctx)
        assert report.overall_status == "fail"
        assert report.failed_count >= 1

    def test_report_serializes(self):
        design = _make_design()
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx)
        d = report.to_dict()
        assert "overall_status" in d
        assert "summary" in d
        assert "results" in d
        assert isinstance(d["results"], list)
        assert len(d["results"]) >= 8

    def test_rule_result_has_required_fields(self):
        design = _make_design()
        constraints = _make_constraints()
        ctx = build_context(design, constraints)
        report = validate_design(ctx)
        for result in report.results:
            d = result.to_dict()
            assert "rule_id" in d
            assert "status" in d
            assert "message" in d
            assert "severity" in d
            assert d["status"] in ("pass", "fail", "skip", "error")
