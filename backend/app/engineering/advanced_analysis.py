"""Advanced Structural Analysis — Buckling, Sizing, Diagrams.

- Euler buckling analysis with effective length factors
- AISC interaction equations (combined axial + bending)
- Member sizing wizard (auto-select lightest adequate section)
- Diagram generation for force/moment/deflection visualization
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from app.engineering.fem_solver import (
    Material, Section, AnalysisResult, ElementForces
)
from app.engineering.sections_db import (
    AISCSection, AISC_W_SHAPES, AISC_HSS_SHAPES, AISC_CHANNEL_SHAPES,
    find_sections_min_Zx, find_sections_min_Ix, get_section,
    SectionType
)


# ── Buckling Analysis ───────────────────────────────────────────────


@dataclass
class BucklingResult:
    """Result of a buckling analysis."""
    critical_load: float       # Euler critical load (N)
    effective_length: float    # m
    effective_length_factor: float  # K
    slenderness_ratio: float   # L_eff / r
    elastic_buckling_stress: float  # Pa
    buckling_mode: str         # 'elastic' | 'inelastic'
    critical_stress: float     # Pa (may differ from elastic if inelastic)
    safety_factor: float = 2.0
    allowable_load: float = 0.0  # Critical / safety factor

    def __post_init__(self):
        self.allowable_load = self.critical_load / self.safety_factor


@dataclass
class InteractionCheck:
    """AISC interaction equation result."""
    equation_used: str      # 'H1-1a' or 'H1-1b'
    demand_ratio: float     # P/Pc + M/Mc — must be <= 1.0
    axial_ratio: float      # P/Pc
    bending_ratio: float    # M/Mc
    demand_capacity_ratio: float  # alias
    status: str             # 'OK' or 'FAIL'
    margin: float = 0.0    # 1.0 - demand_ratio (positive = OK)


def analyze_buckling(
    length: float,
    E: float,
    I: float,
    A: float,
    support_start: str = "fixed",
    support_end: str = "fixed",
    load_type: str = "compression",
) -> BucklingResult:
    """Perform Euler buckling analysis.

    Args:
        length: Member length (m)
        E: Young's modulus (Pa)
        I: Minimum second moment of area (m⁴)
        A: Cross-sectional area (m²)
        support_start: 'fixed', 'pinned', 'free', 'guided'
        support_end: 'fixed', 'pinned', 'free', 'guided'
        load_type: 'compression'

    Returns:
        BucklingResult with critical loads and slenderness
    """
    # Effective length factor K
    K = _effective_length_factor(support_start, support_end)
    L_eff = K * length
    r = math.sqrt(I / A)  # radius of gyration
    slenderness = L_eff / r

    # Euler critical load
    Pe = math.pi ** 2 * E * I / (L_eff ** 2)

    # Elastic buckling stress
    fe = math.pi ** 2 * E / (slenderness ** 2)

    # AISC transition slenderness (4.71 * sqrt(E/Fy))
    Fy = 250e6  # Assume structural steel
    lambda_c = 4.71 * math.sqrt(E / Fy)

    if slenderness <= lambda_c:
        # Inelastic buckling (AISC E3-2)
        Fcr = 0.658 ** (Fy / fe) * Fy
        mode = "inelastic"
    else:
        # Elastic buckling
        Fcr = 0.877 * fe
        mode = "elastic"

    Pcr = Fcr * A  # Modified critical load (AISC approach)

    return BucklingResult(
        critical_load=Pcr,
        effective_length=L_eff,
        effective_length_factor=K,
        slenderness_ratio=slenderness,
        elastic_buckling_stress=fe,
        buckling_mode=mode,
        critical_stress=Fcr,
    )


def _effective_length_factor(start: str, end: str) -> float:
    """Look up K factor from standard cases."""
    K_table = {
        ("fixed", "fixed"): 0.5,
        ("fixed", "pinned"): 0.7,
        ("fixed", "free"): 2.0,
        ("fixed", "guided"): 1.0,
        ("pinned", "pinned"): 1.0,
        ("pinned", "free"): 2.0,
        ("pinned", "guided"): 2.0,
        ("free", "free"): float('inf'),
    }
    return K_table.get((start, end), 1.0)


def check_interaction(
    P: float,       # Axial force (N, positive = compression)
    M: float,       # Bending moment (N·m)
    Pc: float,      # Axial capacity (N)
    Mc: float,      # Moment capacity (N·m)
) -> InteractionCheck:
    """AISC H1 interaction equation for combined axial + bending.

    H1-1a: P/Pc >= 0.2  →  P/Pc + 8/9 * M/Mc <= 1.0
    H1-1b: P/Pc < 0.2   →  P/(2*Pc) + M/Mc <= 1.0
    """
    p_ratio = abs(P) / Pc if Pc > 0 else 0
    m_ratio = abs(M) / Mc if Mc > 0 else 0

    if p_ratio >= 0.2:
        eq = "H1-1a"
        dr = p_ratio + (8 / 9) * m_ratio
    else:
        eq = "H1-1b"
        dr = p_ratio / 2 + m_ratio

    status = "OK" if dr <= 1.0 else "FAIL"

    return InteractionCheck(
        equation_used=eq,
        demand_ratio=dr,
        axial_ratio=p_ratio,
        bending_ratio=m_ratio,
        demand_capacity_ratio=dr,
        status=status,
        margin=1.0 - dr,
    )


# ── Member Sizing Wizard ────────────────────────────────────────────


@dataclass
class SizingResult:
    """Result of the member sizing wizard."""
    optimal_section: str
    section_properties: dict
    utilization_ratio: float  # demand/capacity
    weight_per_length: float  # kg/m
    demand_summary: dict
    all_adequate_sections: list[dict]
    design_notes: str


def size_beam(
    span: float,
    E: float,
    Fy: float,
    V_demand: float,      # Shear demand (N)
    M_demand: float,      # Moment demand (N·m)
    deflection_limit: float = 0,  # L/xxx (e.g., 360 for L/360)
    section_type: SectionType = SectionType.W_SHAPE,
) -> SizingResult:
    """Auto-select lightest adequate beam section.

    Considers:
    - Moment capacity (Zx * Fy)
    - Shear capacity (0.6 * Fy * Aw)
    - Deflection limit (L/limit)
    - Compactness check (λ <= λp)

    Args:
        span: Beam span (m)
        E: Young's modulus (Pa)
        Fy: Yield strength (Pa)
        V_demand: Shear demand (N)
        M_demand: Moment demand (N·m)
        deflection_limit: L/xxx for deflection check (0 = skip)
        section_type: Type of section to consider

    Returns:
        SizingResult with optimal section and all adequate alternatives
    """
    if section_type == SectionType.W_SHAPE:
        all_sections = AISC_W_SHAPES
    elif section_type in (SectionType.HSS_SQ, SectionType.HSS_RECT):
        all_sections = AISC_HSS_SHAPES
    elif section_type == SectionType.CHANNEL:
        all_sections = AISC_CHANNEL_SHAPES
    else:
        all_sections = AISC_W_SHAPES

    adequate = []

    for sec in all_sections:
        # Moment capacity (compact section, Zx * Fy)
        phi_m = 0.9  # LRFD resistance factor
        Mn = phi_m * sec.Zx * Fy  # N·m

        # Shear capacity
        phi_v = 1.0
        Aw = sec.depth * sec.tw  # web area
        Vn = phi_v * 0.6 * Fy * Aw  # N

        # Deflection check
        if deflection_limit > 0:
            I_required = (5 * V_demand * span ** 3) / (384 * E) * deflection_limit / span
            # More accurate: for UDL, delta_max = 5wL⁴/(384EI)
            # For point load at center: delta = PL³/(48EI)
            # Conservative: use UDL formula
            w = V_demand / span if span > 0 else 0
            I_required = (5 * w * span ** 4) / (384 * E) * deflection_limit / span
            if sec.Ix < I_required:
                continue

        # Check capacities
        if Mn >= M_demand and Vn >= V_demand:
            # Compactness check (flange)
            compact_flange = sec.bf_2tf <= 0.38 * math.sqrt(E / Fy) if sec.bf_2tf > 0 else True
            # Compactness check (web)
            compact_web = sec.h_tw <= 3.76 * math.sqrt(E / Fy) if sec.h_tw > 0 else True

            util_m = M_demand / Mn if Mn > 0 else 0
            util_v = V_demand / Vn if Vn > 0 else 0
            utilization = max(util_m, util_v)

            adequate.append({
                "designation": sec.designation,
                "weight_kg_m": round(sec.weight_per_length, 2),
                "Ix_m4": sec.Ix,
                "Zx_m3": sec.Zx,
                "depth_m": sec.depth,
                "moment_capacity_Nm": round(Mn, 0),
                "shear_capacity_N": round(Vn, 0),
                "utilization_ratio": round(utilization, 3),
                "compact": compact_flange and compact_web,
            })

    # Sort by weight (lightest first)
    adequate.sort(key=lambda s: s["weight_kg_m"])

    if not adequate:
        return SizingResult(
            optimal_section="NO ADEQUATE SECTION FOUND",
            section_properties={},
            utilization_ratio=0,
            weight_per_length=0,
            demand_summary={"V": V_demand, "M": M_demand, "span": span},
            all_adequate_sections=[],
            design_notes="Increase section size or reduce demand. Consider W24×76 or larger.",
        )

    best = adequate[0]
    return SizingResult(
        optimal_section=best["designation"],
        section_properties=best,
        utilization_ratio=best["utilization_ratio"],
        weight_per_length=best["weight_kg_m"],
        demand_summary={"V": V_demand, "M": M_demand, "span": span},
        all_adequate_sections=adequate,
        design_notes=(
            f"Lightest adequate: {best['designation']} "
            f"({best['weight_kg_m']} kg/m, "
            f"utilization={best['utilization_ratio']:.1%})"
        ),
    )


def size_column(
    length: float,
    E: float,
    Fy: float,
    P_demand: float,      # Axial demand (N, compression positive)
    K_start: str = "fixed",
    K_end: str = "fixed",
    M_demand: float = 0.0,  # Bending moment if combined loading
    section_type: SectionType = SectionType.W_SHAPE,
) -> SizingResult:
    """Auto-select lightest adequate column section.

    Considers:
    - Yield capacity (Ag * Fy)
    - Euler buckling (AISC E3)
    - Combined axial + bending interaction (AISC H1)
    """
    if section_type == SectionType.W_SHAPE:
        all_sections = AISC_W_SHAPES
    elif section_type in (SectionType.HSS_SQ, SectionType.HSS_RECT):
        all_sections = AISC_HSS_SHAPES
    else:
        all_sections = AISC_W_SHAPES

    adequate = []

    for sec in all_sections:
        # Yield capacity
        Pn_yield = 0.9 * sec.A * Fy  # LRFD

        # Buckling capacity
        K = _effective_length_factor(K_start, K_end)
        L_eff = K * length
        r_min = min(sec.rx, sec.ry) if sec.rx > 0 and sec.ry > 0 else sec.rx
        slenderness = L_eff / r_min

        if slenderness > 0:
            lambda_c = 4.71 * math.sqrt(E / Fy)
            fe = math.pi ** 2 * E / slenderness ** 2

            if slenderness <= lambda_c:
                Fcr = 0.658 ** (Fy / fe) * Fy
            else:
                Fcr = 0.877 * fe

            Pn_buckle = 0.9 * Fcr * sec.A
        else:
            Pn_buckle = Pn_yield

        Pn = min(Pn_yield, Pn_buckle)

        # Moment capacity
        Mc = 0.9 * sec.Zx * Fy

        # Interaction check
        if M_demand > 0:
            ic = check_interaction(P_demand, M_demand, Pn, Mc)
            utilization = ic.demand_capacity_ratio
        else:
            utilization = abs(P_demand) / Pn if Pn > 0 else 0

        if utilization <= 1.0:
            adequate.append({
                "designation": sec.designation,
                "weight_kg_m": round(sec.weight_per_length, 2),
                "Ax_m2": sec.A,
                "Ix_m4": sec.Ix,
                "rx_m": sec.rx,
                "slenderness": round(slenderness, 1),
                "axial_capacity_N": round(Pn, 0),
                "moment_capacity_Nm": round(Mc, 0),
                "utilization_ratio": round(utilization, 3),
                "buckling_governs": Pn_buckle < Pn_yield,
            })

    adequate.sort(key=lambda s: s["weight_kg_m"])

    if not adequate:
        return SizingResult(
            optimal_section="NO ADEQUATE COLUMN FOUND",
            section_properties={},
            utilization_ratio=0,
            weight_per_length=0,
            demand_summary={"P": P_demand, "M": M_demand, "length": length},
            all_adequate_sections=[],
            design_notes="Column demand exceeds all available sections. Consider larger sections or reduce load.",
        )

    best = adequate[0]
    return SizingResult(
        optimal_section=best["designation"],
        section_properties=best,
        utilization_ratio=best["utilization_ratio"],
        weight_per_length=best["weight_kg_m"],
        demand_summary={"P": P_demand, "M": M_demand, "length": length},
        all_adequate_sections=adequate,
        design_notes=(
            f"Lightest adequate: {best['designation']} "
            f"({best['weight_kg_m']} kg/m, "
            f"utilization={best['utilization_ratio']:.1%}, "
            f"slenderness={best['slenderness']})"
        ),
    )


# ── Diagram Generation ──────────────────────────────────────────────


def generate_diagram_data(
    analysis: AnalysisResult,
    element_id: int,
    n_points: int = 50,
) -> dict:
    """Generate diagram data for a specific element.

    Returns dict with:
    - moment: [{x, y}] normalized positions and values
    - shear: [{x, y}]
    - deflection: [{x, y}]
    - max_values: {moment, shear, deflection}
    """
    ef = analysis.element_forces.get(element_id)
    if ef is None:
        return {"error": f"Element {element_id} not found in results"}

    def interpolate(
        raw: list[tuple[float, float]], n: int
    ) -> list[dict]:
        if not raw:
            return [{"x": 0, "y": 0}] * n
        L = raw[-1][0]
        result = []
        for i in range(n):
            x = L * i / (n - 1) if n > 1 else 0
            # Linear interpolation
            y = 0
            for k in range(len(raw) - 1):
                x0, y0 = raw[k]
                x1, y1 = raw[k + 1]
                if x0 <= x <= x1:
                    t = (x - x0) / (x1 - x0) if x1 > x0 else 0
                    y = y0 + t * (y1 - y0)
                    break
            result.append({"x": round(x, 4), "y": round(y, 2)})
        return result

    return {
        "element_id": element_id,
        "moment": interpolate(ef.moment_diagram, n_points),
        "shear": interpolate(ef.shear_diagram, n_points),
        "deflection": interpolate(ef.deflection_diagram, n_points),
        "max_values": {
            "moment_Nm": round(ef.max_moment, 2),
            "shear_N": round(ef.max_shear, 2),
            "deflection_m": round(ef.max_deflection, 6),
        },
    }


def generate_summary_table(analysis: AnalysisResult) -> dict:
    """Generate a summary table of all analysis results."""
    summary = {
        "max_displacement_m": round(analysis.max_displacement, 6),
        "max_axial_force_N": round(analysis.max_axial_force, 0),
        "max_shear_force_N": round(analysis.max_shear_force, 0),
        "max_bending_moment_Nm": round(analysis.max_bending_moment, 0),
        "reactions": {},
        "element_summary": [],
    }

    for node_id, rxn in analysis.reactions.items():
        summary["reactions"][node_id] = {
            "Fx": round(rxn[0], 0),
            "Fy": round(rxn[1], 0),
            "Mz": round(rxn[2], 0),
        }

    for elem_id, ef in analysis.element_forces.items():
        summary["element_summary"].append({
            "element_id": elem_id,
            "max_moment_Nm": round(ef.max_moment, 0),
            "max_shear_N": round(ef.max_shear, 0),
            "max_deflection_m": round(ef.max_deflection, 6),
        })

    return summary
