"""
Engineering Calculations API — Exposes all engineering modules.

Endpoints:
  - POST /engineering/wind-load — ASCE 7 wind pressure calculation
  - POST /engineering/seismic-load — ELF seismic load calculation
  - POST /engineering/optimize — Multi-objective Pareto optimization
  - POST /engineering/cost-estimate — Detailed cost estimation
  - POST /engineering/safety-factors — Member-level safety factors
  - POST /engineering/material-substitution — Material alternative finder
  - POST /engineering/design-diff — Compare two designs
  - GET  /engineering/templates — List project templates
  - GET  /engineering/templates/{id} — Get specific template
  - POST /engineering/generate-report — Generate PDF engineering report
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Any

from app.engineering.wind_load import calculate_wind_loads, WindLoadInput
from app.engineering.seismic_load import calculate_seismic_loads, SeismicLoadInput
from app.engineering.optimization import (
    optimize_designs, DesignCandidate, OptimizationCriteria,
)
from app.engineering.cost_estimation import estimate_cost
from app.engineering.safety_factors import calculate_safety_factors
from app.engineering.material_substitution import recommend_substitutions
from app.engineering.design_diff import compute_design_diff
from app.engineering.templates import list_templates, get_template, get_templates_for_climate
from app.engineering.report_generator import generate_engineering_report

router = APIRouter(prefix="/engineering", tags=["Engineering Calculations"])


# ── Request / Response schemas ──

class WindLoadRequest(BaseModel):
    mean_roof_height_m: float = Field(..., gt=0, le=30)
    plan_length_m: float = Field(..., gt=0, le=100)
    plan_width_m: float = Field(..., gt=0, le=100)
    roof_slope_deg: float = Field(default=0, ge=0, le=60)
    basic_wind_speed_m_s: float | None = Field(default=None, gt=0)
    region: str = "interior_south_asia"
    exposure_category: str = "C"
    risk_category: str = "II"
    enclosure_classification: str = "enclosed"
    topographic_factor: float = 1.0
    importance_factor: float = 1.0
    directionality_factor: float = 0.85


class SeismicLoadRequest(BaseModel):
    total_height_m: float = Field(..., gt=0, le=50)
    number_of_stories: int = Field(default=1, ge=1, le=10)
    structural_system: str = "bamboo_frame"
    region: str = "generic"
    seismic_zone_factor_z: float | None = None
    soil_site_class: str = "D"
    response_modification_r: float | None = None
    importance_factor: float = 1.0
    plan_length_m: float = 5.0
    plan_width_m: float = 4.0
    story_weights_kn: list[float] | None = None


class OptimizationRequest(BaseModel):
    candidates: list[dict[str, Any]]
    cost_weight: float = 0.25
    structural_weight: float = 0.30
    compliance_weight: float = 0.20
    build_complexity_weight: float = 0.15
    material_availability_weight: float = 0.10


class CostEstimateRequest(BaseModel):
    materials: list[dict[str, Any]]
    region: str = "south_asia"
    shelter_type: str = "bamboo_truss"
    occupancy: int = 5
    floor_area_m2: float = 20.0
    transport_distance_km: float = 10.0
    equipment_days: float = 0


class SafetyFactorRequest(BaseModel):
    members: list[dict[str, Any]]
    total_weight_kn: float = 10.0
    base_shear_kn: float = 0.0


class MaterialSubstitutionRequest(BaseModel):
    material_type: str
    max_recommendations: int = 3


class DesignDiffRequest(BaseModel):
    design_a: dict[str, Any]
    design_b: dict[str, Any]


class ReportRequest(BaseModel):
    project_name: str = "Panagah Shelter"
    design_data: dict[str, Any] | None = None
    wind_data: dict[str, Any] | None = None
    seismic_data: dict[str, Any] | None = None
    analysis_data: dict[str, Any] | None = None
    compliance_data: dict[str, Any] | None = None
    cost_data: dict[str, Any] | None = None


# ── Endpoints ──

@router.post("/wind-load", summary="Calculate ASCE 7 wind pressures")
def api_wind_load(req: WindLoadRequest):
    inp = WindLoadInput(
        mean_roof_height_m=req.mean_roof_height_m,
        plan_length_m=req.plan_length_m,
        plan_width_m=req.plan_width_m,
        roof_slope_deg=req.roof_slope_deg,
        basic_wind_speed_m_s=req.basic_wind_speed_m_s,
        region=req.region,
        exposure_category=req.exposure_category,
        risk_category=req.risk_category,
        enclosure_classification=req.enclosure_classification,
        topographic_factor=req.topographic_factor,
        importance_factor=req.importance_factor,
        directionality_factor=req.directionality_factor,
    )
    result = calculate_wind_loads(inp)
    return result.to_dict()


@router.post("/seismic-load", summary="Calculate ELF seismic loads")
def api_seismic_load(req: SeismicLoadRequest):
    inp = SeismicLoadInput(
        total_height_m=req.total_height_m,
        number_of_stories=req.number_of_stories,
        structural_system=req.structural_system,
        region=req.region,
        seismic_zone_factor_z=req.seismic_zone_factor_z,
        soil_site_class=req.soil_site_class,
        response_modification_r=req.response_modification_r,
        importance_factor=req.importance_factor,
        plan_length_m=req.plan_length_m,
        plan_width_m=req.plan_width_m,
        story_weights_kn=req.story_weights_kn,
    )
    result = calculate_seismic_loads(inp)
    return result.to_dict()


@router.post("/optimize", summary="Multi-objective Pareto design optimization")
def api_optimize(req: OptimizationRequest):
    candidates = []
    for c in req.candidates:
        candidates.append(DesignCandidate(
            design_id=c.get("design_id", ""),
            name=c.get("name", ""),
            cost_usd=c.get("cost_usd", 0),
            structural_score=c.get("structural_score", 50),
            compliance_score=c.get("compliance_score", 50),
            build_complexity=c.get("build_complexity", 50),
            material_availability=c.get("material_availability", 50),
            member_count=c.get("member_count", 0),
            span_m=c.get("span_m", 0),
            height_m=c.get("height_m", 0),
            total_weight_kg=c.get("total_weight_kg", 0),
        ))

    criteria = OptimizationCriteria(
        cost_weight=req.cost_weight,
        structural_weight=req.structural_weight,
        compliance_weight=req.compliance_weight,
        build_complexity_weight=req.build_complexity_weight,
        material_availability_weight=req.material_availability_weight,
    )

    result = optimize_designs(candidates, criteria)
    return result.to_dict()


@router.post("/cost-estimate", summary="Detailed cost estimation")
def api_cost_estimate(req: CostEstimateRequest):
    result = estimate_cost(
        materials=req.materials,
        region=req.region,
        shelter_type=req.shelter_type,
        occupancy=req.occupancy,
        floor_area_m2=req.floor_area_m2,
        transport_distance_km=req.transport_distance_km,
        equipment_days=req.equipment_days,
    )
    return result.to_dict()


@router.post("/safety-factors", summary="Member-level safety factor analysis")
def api_safety_factors(req: SafetyFactorRequest):
    result = calculate_safety_factors(
        members=req.members,
        total_weight_kn=req.total_weight_kn,
        base_shear_kn=req.base_shear_kn,
    )
    return result.to_dict()


@router.post("/material-substitution", summary="Find material substitutes")
def api_material_substitution(req: MaterialSubstitutionRequest):
    recs = recommend_substitutions(req.material_type, req.max_recommendations)
    return {
        "original_material": req.material_type,
        "recommendations": [r.to_dict() for r in recs],
    }


@router.post("/design-diff", summary="Compare two designs")
def api_design_diff(req: DesignDiffRequest):
    result = compute_design_diff(req.design_a, req.design_b)
    return result.to_dict()


@router.get("/templates", summary="List project templates")
def api_list_templates(climate: str | None = None):
    if climate:
        return get_templates_for_climate(climate)
    return list_templates()


@router.get("/templates/{template_id}", summary="Get specific template")
def api_get_template(template_id: str):
    t = get_template(template_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return t.to_dict()


@router.post("/generate-report", summary="Generate PDF engineering report")
def api_generate_report(req: ReportRequest):
    pdf_bytes = generate_engineering_report(
        project_name=req.project_name,
        design_data=req.design_data,
        wind_data=req.wind_data,
        seismic_data=req.seismic_data,
        analysis_data=req.analysis_data,
        compliance_data=req.compliance_data,
        cost_data=req.cost_data,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{req.project_name}_report.pdf"'},
    )
