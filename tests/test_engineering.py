"""
Tests for all engineering calculation modules:
  - Wind load engine
  - Seismic load calculator
  - Design optimization (Pareto)
  - Cost estimation
  - Safety factor calculator
  - Material substitution recommender
  - Design diff engine
  - Project templates
  - PDF report generator
"""
import pytest
import math

# ── Wind Load Tests ──

from app.engineering.wind_load import calculate_wind_loads, WindLoadInput


class TestWindLoad:
    def test_basic_calculation(self):
        inp = WindLoadInput(mean_roof_height_m=3.0, plan_length_m=5.0, plan_width_m=4.0)
        result = calculate_wind_loads(inp)
        assert result.velocity_pressure_pa > 0
        assert result.governing_pressure_pa > 0
        assert len(result.zones) == 6

    def test_coastal_higher_pressure(self):
        coastal = calculate_wind_loads(WindLoadInput(
            mean_roof_height_m=3.0, plan_length_m=5.0, plan_width_m=4.0, region="coastal_south_asia"
        ))
        interior = calculate_wind_loads(WindLoadInput(
            mean_roof_height_m=3.0, plan_length_m=5.0, plan_width_m=4.0, region="interior_south_asia"
        ))
        assert coastal.governing_pressure_pa > interior.governing_pressure_pa

    def test_exposure_affects_pressure(self):
        exp_b = calculate_wind_loads(WindLoadInput(
            mean_roof_height_m=3.0, plan_length_m=5.0, plan_width_m=4.0, exposure_category="B"
        ))
        exp_d = calculate_wind_loads(WindLoadInput(
            mean_roof_height_m=3.0, plan_length_m=5.0, plan_width_m=4.0, exposure_category="D"
        ))
        assert exp_d.governing_pressure_pa > exp_b.governing_pressure_pa

    def test_partial_enclosure_higher_internal_pressure(self):
        enclosed = calculate_wind_loads(WindLoadInput(
            mean_roof_height_m=3.0, plan_length_m=5.0, plan_width_m=4.0, enclosure_classification="enclosed"
        ))
        partial = calculate_wind_loads(WindLoadInput(
            mean_roof_height_m=3.0, plan_length_m=5.0, plan_width_m=4.0, enclosure_classification="partially_enclosed"
        ))
        assert partial.gcpi > enclosed.gcpi

    def test_result_serializes(self):
        result = calculate_wind_loads(WindLoadInput(
            mean_roof_height_m=3.0, plan_length_m=5.0, plan_width_m=4.0
        ))
        d = result.to_dict()
        assert "velocity_pressure_pa" in d
        assert "zones" in d
        assert "safety_assessment" in d
        assert "reference" in d
        assert len(d["zones"]) == 6


# ── Seismic Load Tests ──

from app.engineering.seismic_load import calculate_seismic_loads, SeismicLoadInput


class TestSeismicLoad:
    def test_basic_calculation(self):
        inp = SeismicLoadInput(total_height_m=3.0, number_of_stories=1)
        result = calculate_seismic_loads(inp)
        assert result.base_shear_kn > 0
        assert result.total_weight_kn > 0
        assert len(result.story_forces) == 1

    def test_multi_story(self):
        inp = SeismicLoadInput(total_height_m=6.0, number_of_stories=2)
        result = calculate_seismic_loads(inp)
        assert len(result.story_forces) == 2
        assert result.story_forces[0].lateral_force_kn > 0

    def test_higher_zone_more_shear(self):
        low = calculate_seismic_loads(SeismicLoadInput(
            total_height_m=3.0, region="punjab"
        ))
        high = calculate_seismic_loads(SeismicLoadInput(
            total_height_m=3.0, region="kashmir"
        ))
        assert high.base_shear_kn > low.base_shear_kn

    def test_soil_class_matters(self):
        rock = calculate_seismic_loads(SeismicLoadInput(
            total_height_m=3.0, soil_site_class="B"
        ))
        soft = calculate_seismic_loads(SeismicLoadInput(
            total_height_m=3.0, soil_site_class="E"
        ))
        assert soft.base_shear_kn > rock.base_shear_kn

    def test_result_serializes(self):
        result = calculate_seismic_loads(SeismicLoadInput(total_height_m=3.0))
        d = result.to_dict()
        assert "parameters" in d
        assert "results" in d
        assert "story_forces" in d
        assert "safety_assessment" in d


# ── Design Optimization Tests ──

from app.engineering.optimization import (
    optimize_designs, DesignCandidate, OptimizationCriteria,
)


class TestOptimization:
    def _make_candidates(self):
        return [
            DesignCandidate("d1", "Cheap Simple", cost_usd=200, structural_score=60, compliance_score=70, build_complexity=30, material_availability=90),
            DesignCandidate("d2", "Strong Expensive", cost_usd=800, structural_score=95, compliance_score=90, build_complexity=70, material_availability=60),
            DesignCandidate("d3", "Balanced", cost_usd=450, structural_score=80, compliance_score=85, build_complexity=50, material_availability=75),
            DesignCandidate("d4", "Poor All", cost_usd=600, structural_score=40, compliance_score=50, build_complexity=80, material_availability=40),
        ]

    def test_optimization_runs(self):
        candidates = self._make_candidates()
        result = optimize_designs(candidates)
        assert len(result.candidates) == 4
        assert len(result.pareto_front) >= 1

    def test_pareto_front_dominates(self):
        candidates = self._make_candidates()
        result = optimize_designs(candidates)
        for p in result.pareto_front:
            assert p.is_pareto_optimal

    def test_best_value_is_top_scored(self):
        candidates = self._make_candidates()
        result = optimize_designs(candidates)
        assert result.best_value is not None
        assert result.best_value.weighted_score >= result.candidates[-1].weighted_score

    def test_empty_candidates(self):
        result = optimize_designs([])
        assert result.summary["total_candidates"] == 0

    def test_custom_criteria(self):
        candidates = self._make_candidates()
        criteria = OptimizationCriteria(cost_weight=0.5, structural_weight=0.5)
        result = optimize_designs(candidates, criteria)
        assert len(result.candidates) == 4

    def test_serialization(self):
        result = optimize_designs(self._make_candidates())
        d = result.to_dict()
        assert "candidates" in d
        assert "pareto_front" in d
        assert "recommendations" in d


# ── Cost Estimation Tests ──

from app.engineering.cost_estimation import estimate_cost


class TestCostEstimation:
    def test_basic_estimate(self):
        materials = [
            {"type": "treated_bamboo", "qty": 20, "unit_cost_usd": 3.50},
            {"type": "corrugated_tin", "qty": 8, "unit_cost_usd": 12.00},
        ]
        result = estimate_cost(materials, region="south_asia", occupancy=5)
        assert result.summary.total_cost_usd > 0
        assert result.summary.cost_per_person_usd > 0
        assert len(result.line_items) > 0

    def test_transport_affects_cost(self):
        materials = [{"type": "treated_bamboo", "qty": 20}]
        close = estimate_cost(materials, transport_distance_km=5)
        far = estimate_cost(materials, transport_distance_km=100)
        assert far.summary.transport_cost_usd > close.summary.transport_cost_usd

    def test_equipment_adds_cost(self):
        materials = [{"type": "treated_bamboo", "qty": 20}]
        no_equip = estimate_cost(materials, equipment_days=0)
        with_equip = estimate_cost(materials, equipment_days=5)
        assert with_equip.summary.equipment_cost_usd > no_equip.summary.equipment_cost_usd

    def test_contingency_present(self):
        materials = [{"type": "treated_bamboo", "qty": 20}]
        result = estimate_cost(materials)
        assert result.summary.contingency_cost_usd > 0

    def test_serialization(self):
        result = estimate_cost([{"type": "treated_bamboo", "qty": 20}])
        d = result.to_dict()
        assert "line_items" in d
        assert "summary" in d
        assert "assumptions" in d


# ── Safety Factor Tests ──

from app.engineering.safety_factors import calculate_safety_factors


class TestSafetyFactors:
    def test_basic_calculation(self):
        members = [
            {"id": "m1", "type": "column", "material_id": "treated_bamboo", "length_m": 2.5, "diameter_m": 0.10},
            {"id": "m2", "type": "beam", "material_id": "treated_bamboo", "length_m": 5.0, "diameter_m": 0.10},
        ]
        result = calculate_safety_factors(members, total_weight_kn=10.0)
        assert result.total_members == 2
        assert result.overall_min_sf > 0
        assert len(result.members) == 2

    def test_larger_diameter_safer(self):
        small = [{"id": "m1", "type": "column", "material_id": "treated_bamboo", "length_m": 2.5, "diameter_m": 0.06}]
        large = [{"id": "m1", "type": "column", "material_id": "treated_bamboo", "length_m": 2.5, "diameter_m": 0.15}]
        r_small = calculate_safety_factors(small)
        r_large = calculate_safety_factors(large)
        assert r_large.overall_min_sf > r_small.overall_min_sf

    def test_serialization(self):
        members = [{"id": "m1", "type": "column", "material_id": "treated_bamboo", "length_m": 2.5, "diameter_m": 0.10}]
        result = calculate_safety_factors(members)
        d = result.to_dict()
        assert "members" in d
        assert "summary" in d


# ── Material Substitution Tests ──

from app.engineering.material_substitution import recommend_substitutions


class TestMaterialSubstitution:
    def test_bamboo_substitutes(self):
        recs = recommend_substitutions("treated_bamboo")
        assert len(recs) > 0
        assert all(r.compatibility_score > 0 for r in recs)

    def test_no_self_substitution(self):
        recs = recommend_substitutions("treated_bamboo")
        assert all(r.recommended_type != "treated_bamboo" for r in recs)

    def test_sorted_by_score(self):
        recs = recommend_substitutions("treated_bamboo")
        scores = [r.compatibility_score for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_unknown_material(self):
        recs = recommend_substitutions("unobtainium")
        assert len(recs) == 0

    def test_serialization(self):
        recs = recommend_substitutions("treated_bamboo")
        assert all(hasattr(r, "to_dict") for r in recs)


# ── Design Diff Tests ──

from app.engineering.design_diff import compute_design_diff


class TestDesignDiff:
    def test_identical_designs(self):
        d = {"version": "A", "span_m": 5.0, "height_m": 2.5, "members": [{"id": "m1", "type": "beam"}], "connections": []}
        result = compute_design_diff(d, d)
        assert len(result.changes) == 0
        assert "identical" in result.recommendation.lower()

    def test_member_added(self):
        a = {"version": "A", "span_m": 5.0, "height_m": 2.5, "members": [], "connections": []}
        b = {"version": "B", "span_m": 5.0, "height_m": 2.5, "members": [{"id": "m1", "type": "beam"}], "connections": []}
        result = compute_design_diff(a, b)
        assert any(c.category == "member_added" for c in result.changes)

    def test_geometry_change(self):
        a = {"version": "A", "span_m": 5.0, "height_m": 2.5, "members": [], "connections": []}
        b = {"version": "B", "span_m": 6.0, "height_m": 2.5, "members": [], "connections": []}
        result = compute_design_diff(a, b)
        assert any(c.category == "geometry_changed" for c in result.changes)

    def test_serialization(self):
        a = {"version": "A", "span_m": 5.0, "height_m": 2.5, "members": [], "connections": []}
        b = {"version": "B", "span_m": 6.0, "height_m": 3.0, "members": [{"id": "m1", "type": "beam"}], "connections": []}
        result = compute_design_diff(a, b)
        d = result.to_dict()
        assert "changes" in d
        assert "summary" in d
        assert "recommendation" in d


# ── Templates Tests ──

from app.engineering.templates import list_templates, get_template, get_templates_for_climate


class TestTemplates:
    def test_list_templates(self):
        templates = list_templates()
        assert len(templates) >= 4

    def test_get_template(self):
        t = get_template("T-EMERGENCY-001")
        assert t is not None
        assert t.name == "Emergency Family Shelter"

    def test_unknown_template(self):
        assert get_template("NONEXISTENT") is None

    def test_filter_by_climate(self):
        tropical = get_templates_for_climate("tropical")
        assert len(tropical) >= 1

    def test_all_templates_have_required_fields(self):
        for t in list_templates():
            assert "template_id" in t
            assert "name" in t
            assert "suggested_materials" in t
            assert "estimated_cost_usd" in t


# ── PDF Report Tests ──

from app.engineering.report_generator import generate_engineering_report


class TestReportGenerator:
    def test_basic_report(self):
        pdf = generate_engineering_report(
            project_name="Test Project",
            design_data={"span_m": 5.0, "height_m": 2.5},
        )
        assert len(pdf) > 0
        assert pdf[:4] == b"%PDF"

    def test_full_report(self):
        pdf = generate_engineering_report(
            project_name="Full Test",
            design_data={"span_m": 5.0, "height_m": 2.5, "members": 12},
            wind_data={
                "wind_speed_m_s": 35.0, "wind_speed_kmh": 126.0,
                "velocity_pressure_pa": 450.0, "velocity_pressure_kpa": 0.45,
                "coefficients": {"kz": 1.01, "kzt": 1.0, "kd": 0.85, "gust_effect_factor": 0.85},
                "zones": [{"zone_name": "Zone 1", "surface": "wall", "positive_pa": 100, "negative_pa": -150, "net_pa": -150}],
                "governing_pressure_pa": 150.0, "governing_pressure_kpa": 0.15,
                "governing_zone": "zone_5",
                "safety_assessment": {"is_wind_resistant": True, "safety_margin": 2.5, "assessment": "Adequate"},
            },
            seismic_data={
                "parameters": {"zone_factor_z": 0.24, "spectral_acceleration_ss": 1.0, "design_sds": 0.67, "response_modification_r": 3.0, "fundamental_period_s": 0.3, "seismic_response_coefficient_cs": 0.22},
                "results": {"total_weight_kn": 15.0, "base_shear_kn": 3.3, "base_shear_coefficient": 0.22, "max_lateral_force_kn": 3.3, "max_overturning_moment_knm": 9.9},
                "safety_assessment": {"is_seismically_designed": True, "safety_margin": 2.0, "assessment": "Adequate"},
            },
            compliance_data={
                "status": "pass",
                "standard": "Sphere Handbook V24.1",
                "summary": {"total": 8, "pass": 8, "review": 0, "fail": 0},
            },
            cost_data={
                "summary": {
                    "total_cost_usd": 450.0, "material_cost_usd": 200.0,
                    "labor_cost_usd": 150.0, "transport_cost_usd": 30.0,
                    "contingency_cost_usd": 50.0,
                    "cost_per_person_usd": 90.0, "cost_per_m2_usd": 22.5,
                },
            },
        )
        assert len(pdf) > 500
        assert pdf[:4] == b"%PDF"
