"""Advanced Engineering API — FEM Solver, Sections, Buckling, Sizing, Diagrams.

Endpoints:
- POST /api/v1/fem/analyze        — Run 2D frame analysis (Direct Stiffness Method)
- POST /api/v1/fem/beam           — Quick simply-supported beam analysis
- POST /api/v1/fem/portal-frame   — Quick portal frame analysis
- GET  /api/v1/sections           — List all AISC sections
- GET  /api/v1/sections/{type}    — List sections by type
- GET  /api/v1/sections/lookup/{designation} — Get specific section
- POST /api/v1/sections/find      — Find sections matching criteria
- POST /api/v1/buckling           — Euler buckling analysis
- POST /api/v1/interaction-check  — AISC H1 interaction equation
- POST /api/v1/sizing/beam        — Auto-size beam
- POST /api/v1/sizing/column      — Auto-size column
- POST /api/v1/diagrams           — Generate force/moment/deflection diagrams
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.engineering.fem_solver import (
    FEMSolver2D, Node, Element, Material, Section,
    PointLoad, DistributedLoad, SupportType,
    analyze_simple_beam, analyze_portal_frame,
)
from app.engineering.sections_db import (
    get_section, get_sections_by_type, find_sections_in_range,
    list_all_designations, AISC_W_SHAPES, AISC_HSS_SHAPES,
    AISC_CHANNEL_SHAPES, SectionType, AISCSection
)
from app.engineering.advanced_analysis import (
    analyze_buckling, check_interaction, size_beam, size_column,
    generate_diagram_data, generate_summary_table,
)

router = APIRouter(tags=["Advanced Engineering"])


# ── Request/Response Models ─────────────────────────────────────────


class FEMNodeRequest(BaseModel):
    id: int
    x: float
    y: float
    z: float = 0.0
    support: str = "free"  # free, pinned, fixed, roller_x, roller_y


class FEMElementRequest(BaseModel):
    id: int
    node_i: int
    node_j: int
    E: float = 200e9  # Default steel
    A: float = 0.01  # Default 100 cm²
    Ix: float = 1e-4  # Default
    release_i: bool = False
    release_j: bool = False


class FEMPointLoadRequest(BaseModel):
    node_id: int
    fx: float = 0.0
    fy: float = 0.0
    mz: float = 0.0


class FEMDistLoadRequest(BaseModel):
    element_id: int
    wy: float = 0.0


class FEMAnalyzeRequest(BaseModel):
    nodes: list[FEMNodeRequest]
    elements: list[FEMElementRequest]
    point_loads: list[FEMPointLoadRequest] = []
    distributed_loads: list[FEMDistLoadRequest] = []


class BeamAnalysisRequest(BaseModel):
    length: float = Field(..., description="Span length (m)")
    E: float = Field(200e9, description="Young's modulus (Pa)")
    I: float = Field(1e-4, description="Second moment of area (m⁴)")
    A: float = Field(0.01, description="Cross-sectional area (m²)")
    loads: list[dict] = Field(..., description="List of loads")
    n_elements: int = Field(10, description="Number of elements")


class PortalFrameRequest(BaseModel):
    width: float = Field(..., description="Frame width (m)")
    height: float = Field(..., description="Column height (m)")
    E: float = Field(200e9, description="Young's modulus (Pa)")
    I_col: float = Field(5e-5, description="Column I (m⁴)")
    I_beam: float = Field(1e-4, description="Beam I (m⁴)")
    A_col: float = Field(0.005, description="Column area (m²)")
    A_beam: float = Field(0.01, description="Beam area (m²)")
    loads: list[dict] = Field(..., description="Loads on beam")


class BucklingRequest(BaseModel):
    length: float = Field(..., description="Member length (m)")
    E: float = Field(200e9, description="Young's modulus (Pa)")
    I: float = Field(..., description="Min moment of inertia (m⁴)")
    A: float = Field(..., description="Cross-sectional area (m²)")
    support_start: str = Field("fixed")
    support_end: str = Field("fixed")


class InteractionCheckRequest(BaseModel):
    P: float = Field(..., description="Axial force (N)")
    M: float = Field(..., description="Bending moment (N·m)")
    Pc: float = Field(..., description="Axial capacity (N)")
    Mc: float = Field(..., description="Moment capacity (N·m)")


class BeamSizingRequest(BaseModel):
    span: float = Field(..., description="Beam span (m)")
    E: float = Field(200e9, description="Young's modulus (Pa)")
    Fy: float = Field(250e6, description="Yield strength (Pa)")
    V_demand: float = Field(..., description="Shear demand (N)")
    M_demand: float = Field(..., description="Moment demand (N·m)")
    deflection_limit: float = Field(360, description="L/xxx deflection limit")


class ColumnSizingRequest(BaseModel):
    length: float = Field(..., description="Column length (m)")
    E: float = Field(200e9, description="Young's modulus (Pa)")
    Fy: float = Field(250e6, description="Yield strength (Pa)")
    P_demand: float = Field(..., description="Axial demand (N)")
    M_demand: float = Field(0.0, description="Moment demand (N·m)")
    K_start: str = Field("fixed")
    K_end: str = Field("fixed")


class DiagramRequest(BaseModel):
    nodes: list[FEMNodeRequest]
    elements: list[FEMElementRequest]
    point_loads: list[FEMPointLoadRequest] = []
    distributed_loads: list[FEMDistLoadRequest] = []
    element_id: int = Field(..., description="Element to diagram")
    n_points: int = Field(50, description="Number of data points")


class SectionFindRequest(BaseModel):
    min_Ix: Optional[float] = None
    min_Zx: Optional[float] = None
    depth_min: Optional[float] = None
    depth_max: Optional[float] = None
    weight_min: Optional[float] = None
    weight_max: Optional[float] = None
    section_type: Optional[str] = None


# ── FEM Solver Endpoints ────────────────────────────────────────────


@router.post("/fem/analyze", summary="Run 2D frame analysis (Direct Stiffness Method)")
def fem_analyze(req: FEMAnalyzeRequest):
    """Run a full 2D structural analysis using the Direct Stiffness Method.

    Provides displacements, reactions, and internal forces for all elements.
    """
    solver = FEMSolver2D()

    for n in req.nodes:
        solver.add_node(Node(
            id=n.id, x=n.x, y=n.y, z=n.z,
            support=SupportType(n.support),
        ))

    for e in req.elements:
        mat = Material(name="Custom", E=e.E)
        sec = Section(name="Custom", A=e.A, Ix=e.Ix)
        solver.add_element(Element(
            id=e.id, node_i=e.node_i, node_j=e.node_j,
            material=mat, section=sec,
            release_i=e.release_i, release_j=e.release_j,
        ))

    for pl in req.point_loads:
        solver.add_point_load(PointLoad(
            node_id=pl.node_id, fx=pl.fx, fy=pl.fy, mz=pl.mz,
        ))

    for dl in req.distributed_loads:
        solver.add_distributed_load(DistributedLoad(
            element_id=dl.element_id, wy=dl.wy,
        ))

    result = solver.solve()

    return {
        "success": result.success,
        "message": result.message,
        "max_displacement_m": round(result.max_displacement, 6),
        "max_axial_force_N": round(result.max_axial_force, 0),
        "max_shear_force_N": round(result.max_shear_force, 0),
        "max_bending_moment_Nm": round(result.max_bending_moment, 0),
        "displacements": {
            str(k): [round(v, 6) for v in d]
            for k, d in result.displacements.items()
        },
        "reactions": {
            str(k): [round(v, 0) for v in r]
            for k, r in result.reactions.items()
        },
        "element_forces": {
            str(k): {
                "axial_N": round(v.ni, 0),
                "shear_y_N": round(v.viy, 0),
                "moment_z_Nm": round(v.miz, 0),
                "max_moment_Nm": round(v.max_moment, 0),
                "max_shear_N": round(v.max_shear, 0),
                "max_deflection_m": round(v.max_deflection, 6),
            }
            for k, v in result.element_forces.items()
        },
    }


@router.post("/fem/beam", summary="Quick simply-supported beam analysis")
def fem_beam(req: BeamAnalysisRequest):
    """Analyze a simply supported beam with given loads."""
    result = analyze_simple_beam(
        L=req.length, E=req.E, I=req.I, A=req.A,
        loads=req.loads, n_elements=req.n_elements,
    )
    summary = generate_summary_table(result)
    return {
        "success": result.success,
        "message": result.message,
        "summary": summary,
    }


@router.post("/fem/portal-frame", summary="Quick portal frame analysis")
def fem_portal_frame(req: PortalFrameRequest):
    """Analyze a portal frame (2 columns + 1 beam)."""
    result = analyze_portal_frame(
        width=req.width, height=req.height,
        E=req.E, I_col=req.I_col, I_beam=req.I_beam,
        A_col=req.A_col, A_beam=req.A_beam,
        loads=req.loads,
    )
    summary = generate_summary_table(result)
    return {
        "success": result.success,
        "message": result.message,
        "summary": summary,
    }


# ── Sections Database Endpoints ─────────────────────────────────────


@router.get("/sections", summary="List all AISC sections")
def list_sections():
    """Get all available sections with their properties."""
    return {
        "total": len(list_all_designations()),
        "w_shapes": len(AISC_W_SHAPES),
        "hss_shapes": len(AISC_HSS_SHAPES),
        "channels": len(AISC_CHANNEL_SHAPES),
        "designations": list_all_designations(),
    }


@router.get("/sections/{section_type}", summary="List sections by type")
def get_sections_by_type_endpoint(section_type: str):
    """Get all sections of a given type (W, HSS-R, HSS-S, C, L)."""
    try:
        st = SectionType(section_type)
    except ValueError:
        raise HTTPException(400, f"Invalid type: {section_type}. Use: W, HSS-R, HSS-S, C, L")

    sections = get_sections_by_type(st)
    return {
        "type": section_type,
        "count": len(sections),
        "sections": [
            {
                "designation": s.designation,
                "depth_m": round(s.depth, 4),
                "width_m": round(s.width, 4),
                "A_m2": s.A,
                "Ix_m4": s.Ix,
                "Iy_m4": s.Iy,
                "Zx_m3": s.Zx,
                "weight_kg_m": s.weight_per_length,
            }
            for s in sections
        ],
    }


@router.get("/sections/lookup/{designation}", summary="Get specific section")
def lookup_section(designation: str):
    """Look up a section by its designation (e.g., W12x50)."""
    sec = get_section(designation)
    if not sec:
        raise HTTPException(404, f"Section '{designation}' not found")
    return {
        "designation": sec.designation,
        "type": sec.section_type.value,
        "depth_m": round(sec.depth, 4),
        "width_m": round(sec.width, 4),
        "tw_m": sec.tw,
        "tf_m": sec.tf,
        "A_m2": sec.A,
        "Ix_m4": sec.Ix,
        "Iy_m4": sec.Iy,
        "Zx_m3": sec.Zx,
        "Zy_m3": sec.Zy,
        "Sx_m3": sec.Sx,
        "Sy_m3": sec.Sy,
        "rx_m": sec.rx,
        "ry_m": sec.ry,
        "J_m4": sec.J,
        "weight_kg_m": sec.weight_per_length,
        "bf_2tf": sec.bf_2tf,
        "h_tw": sec.h_tw,
    }


@router.post("/sections/find", summary="Find sections matching criteria")
def find_sections(req: SectionFindRequest):
    """Find sections matching given constraints."""
    sections = AISC_W_SHAPES + AISC_HSS_SHAPES + AISC_CHANNEL_SHAPES

    if req.section_type:
        sections = [s for s in sections if s.section_type.value == req.section_type]
    if req.min_Ix is not None:
        sections = [s for s in sections if s.Ix >= req.min_Ix]
    if req.min_Zx is not None:
        sections = [s for s in sections if s.Zx >= req.min_Zx]
    if req.depth_min is not None:
        sections = [s for s in sections if s.depth >= req.depth_min]
    if req.depth_max is not None:
        sections = [s for s in sections if s.depth <= req.depth_max]
    if req.weight_min is not None:
        sections = [s for s in sections if s.weight_per_length >= req.weight_min]
    if req.weight_max is not None:
        sections = [s for s in sections if s.weight_per_length <= req.weight_max]

    sections.sort(key=lambda s: s.weight_per_length)

    return {
        "count": len(sections),
        "sections": [
            {
                "designation": s.designation,
                "depth_m": round(s.depth, 4),
                "A_m2": s.A,
                "Ix_m4": s.Ix,
                "Zx_m3": s.Zx,
                "weight_kg_m": s.weight_per_length,
            }
            for s in sections
        ],
    }


# ── Buckling & Interaction Endpoints ────────────────────────────────


@router.post("/buckling", summary="Euler buckling analysis")
def buckling_endpoint(req: BucklingRequest):
    """Perform buckling analysis for a compression member.

    Uses AISC Chapter E for column buckling.
    """
    result = analyze_buckling(
        length=req.length, E=req.E, I=req.I, A=req.A,
        support_start=req.support_start, support_end=req.support_end,
    )
    return {
        "critical_load_N": round(result.critical_load, 0),
        "critical_stress_Pa": round(result.critical_stress, 0),
        "effective_length_m": round(result.effective_length, 4),
        "effective_length_factor_K": result.effective_length_factor,
        "slenderness_ratio": round(result.slenderness_ratio, 1),
        "buckling_mode": result.buckling_mode,
        "elastic_buckling_stress_Pa": round(result.elastic_buckling_stress, 0),
        "safety_factor": result.safety_factor,
        "allowable_load_N": round(result.allowable_load, 0),
    }


@router.post("/interaction-check", summary="AISC H1 interaction equation")
def interaction_check_endpoint(req: InteractionCheckRequest):
    """Check combined axial + bending per AISC H1."""
    result = check_interaction(req.P, req.M, req.Pc, req.Mc)
    return {
        "equation": result.equation_used,
        "demand_capacity_ratio": round(result.demand_capacity_ratio, 3),
        "axial_ratio": round(result.axial_ratio, 3),
        "bending_ratio": round(result.bending_ratio, 3),
        "status": result.status,
        "margin": round(result.margin, 3),
    }


# ── Member Sizing Endpoints ─────────────────────────────────────────


@router.post("/sizing/beam", summary="Auto-size beam section")
def sizing_beam_endpoint(req: BeamSizingRequest):
    """Automatically select the lightest adequate beam section from AISC database."""
    result = size_beam(
        span=req.span, E=req.E, Fy=req.Fy,
        V_demand=req.V_demand, M_demand=req.M_demand,
        deflection_limit=req.deflection_limit,
    )
    return {
        "optimal_section": result.optimal_section,
        "section_properties": result.section_properties,
        "utilization_ratio": result.utilization_ratio,
        "weight_per_length_kg_m": result.weight_per_length,
        "demand_summary": result.demand_summary,
        "alternatives": result.all_adequate_sections[:5],  # Top 5
        "design_notes": result.design_notes,
        "total_adequate": len(result.all_adequate_sections),
    }


@router.post("/sizing/column", summary="Auto-size column section")
def sizing_column_endpoint(req: ColumnSizingRequest):
    """Automatically select the lightest adequate column section."""
    result = size_column(
        length=req.length, E=req.E, Fy=req.Fy,
        P_demand=req.P_demand, M_demand=req.M_demand,
        K_start=req.K_start, K_end=req.K_end,
    )
    return {
        "optimal_section": result.optimal_section,
        "section_properties": result.section_properties,
        "utilization_ratio": result.utilization_ratio,
        "weight_per_length_kg_m": result.weight_per_length,
        "demand_summary": result.demand_summary,
        "alternatives": result.all_adequate_sections[:5],
        "design_notes": result.design_notes,
        "total_adequate": len(result.all_adequate_sections),
    }


# ── Diagram Generation Endpoint ─────────────────────────────────────


@router.post("/diagrams", summary="Generate force/moment/deflection diagrams")
def diagrams_endpoint(req: DiagramRequest):
    """Run analysis and generate diagram data for a specific element.

    Returns normalized diagram data for rendering in the frontend:
    - Moment diagram (M vs x)
    - Shear force diagram (V vs x)
    - Deflection diagram (δ vs x)
    """
    solver = FEMSolver2D()

    for n in req.nodes:
        solver.add_node(Node(
            id=n.id, x=n.x, y=n.y, z=n.z,
            support=SupportType(n.support),
        ))

    for e in req.elements:
        mat = Material(name="Custom", E=e.E)
        sec = Section(name="Custom", A=e.A, Ix=e.Ix)
        solver.add_element(Element(
            id=e.id, node_i=e.node_i, node_j=e.node_j,
            material=mat, section=sec,
            release_i=e.release_i, release_j=e.release_j,
        ))

    for pl in req.point_loads:
        solver.add_point_load(PointLoad(
            node_id=pl.node_id, fx=pl.fx, fy=pl.fy, mz=pl.mz,
        ))

    for dl in req.distributed_loads:
        solver.add_distributed_load(DistributedLoad(
            element_id=dl.element_id, wy=dl.wy,
        ))

    result = solver.solve()

    if not result.success:
        raise HTTPException(400, result.message)

    diagrams = generate_diagram_data(result, req.element_id, req.n_points)
    summary = generate_summary_table(result)

    return {
        "success": True,
        "diagrams": diagrams,
        "summary": summary,
    }
