"""
Safety Factor Calculator — Member-level structural safety assessment.

Computes actual safety factors for each structural member by comparing
demand (from load analysis) to capacity (from material properties and
cross-section geometry).

Safety Factor = Capacity / Demand

A safety factor ≥ 2.0 is generally acceptable for emergency shelters.
A safety factor ≥ 1.5 is the minimum for humanitarian structures.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.materials.catalog import MATERIAL_CATALOG, MaterialProperties


@dataclass
class MemberSafetyResult:
    """Safety factor analysis for one structural member."""
    member_id: str
    member_type: str
    material_type: str
    length_m: float
    diameter_m: float

    # Capacity
    axial_capacity_kn: float
    bending_capacity_kn: float
    shear_capacity_kn: float

    # Demand (simplified)
    axial_demand_kn: float
    bending_demand_kn: float
    shear_demand_kn: float

    # Safety factors
    axial_sf: float
    bending_sf: float
    shear_sf: float
    governing_sf: float
    governing_mode: str

    # Status
    is_safe: bool
    assessment: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_id": self.member_id,
            "member_type": self.member_type,
            "material": self.material_type,
            "length_m": round(self.length_m, 3),
            "diameter_m": round(self.diameter_m, 4),
            "capacity": {
                "axial_kn": round(self.axial_capacity_kn, 2),
                "bending_kn": round(self.bending_capacity_kn, 2),
                "shear_kn": round(self.shear_capacity_kn, 2),
            },
            "demand": {
                "axial_kn": round(self.axial_demand_kn, 2),
                "bending_kn": round(self.bending_demand_kn, 2),
                "shear_kn": round(self.shear_demand_kn, 2),
            },
            "safety_factors": {
                "axial": round(self.axial_sf, 2),
                "bending": round(self.bending_sf, 2),
                "shear": round(self.shear_sf, 2),
                "governing": round(self.governing_sf, 2),
                "governing_mode": self.governing_mode,
            },
            "is_safe": self.is_safe,
            "assessment": self.assessment,
        }


@dataclass
class SafetyFactorReport:
    """Complete safety factor report for all members."""
    members: list[MemberSafetyResult]
    overall_min_sf: float
    overall_avg_sf: float
    members_safe: int
    members_unsafe: int
    total_members: int
    overall_assessment: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "members": [m.to_dict() for m in self.members],
            "summary": {
                "total_members": self.total_members,
                "members_safe": self.members_safe,
                "members_unsafe": self.members_unsafe,
                "safety_rate": round(self.members_safe / max(self.total_members, 1) * 100, 1),
                "minimum_safety_factor": round(self.overall_min_sf, 2),
                "average_safety_factor": round(self.overall_avg_sf, 2),
            },
            "overall_assessment": self.overall_assessment,
        }


# -------------------------------------------------------------------
# Capacity calculations
# -------------------------------------------------------------------

def _axial_capacity(material: MaterialProperties, diameter_m: float) -> float:
    """Compute axial (compression) capacity in kN.
    
    P = σ_allowable × A
    where A = π/4 × d² × hollow_section_factor
    """
    area = math.pi / 4.0 * diameter_m ** 2 * material.hollow_section_factor
    force_n = material.allowable_axial_stress_pa * area
    return force_n / 1000.0  # Convert N to kN


def _bending_capacity(material: MaterialProperties, diameter_m: float, length_m: float) -> float:
    """Compute bending capacity in kN (simplified as point load at midspan).
    
    M = σ_allowable × I / y
    For circular hollow section: I = π/64 × d⁴ × hsf, y = d/2
    Point load capacity: P = 4M / L
    """
    I = math.pi / 64.0 * diameter_m ** 4 * material.hollow_section_factor
    y = diameter_m / 2.0
    moment_capacity = material.allowable_bending_stress_pa * I / y
    point_load = 4.0 * moment_capacity / max(length_m, 0.1)
    return point_load / 1000.0  # Convert N to kN


def _shear_capacity(material: MaterialProperties, diameter_m: float) -> float:
    """Compute shear capacity in kN.
    
    V = τ_allowable × A_shear
    For circular section: A_shear ≈ 2A/3 (simplified)
    τ_allowable ≈ 0.6 × σ_allowable (von Mises approximation)
    """
    area = math.pi / 4.0 * diameter_m ** 2 * material.hollow_section_factor
    shear_area = 2.0 * area / 3.0
    tau_allowable = 0.6 * material.allowable_axial_stress_pa
    force_n = tau_allowable * shear_area
    return force_n / 1000.0


# -------------------------------------------------------------------
# Demand estimation (simplified)
# -------------------------------------------------------------------

def _estimate_demand(
    member_type: str,
    length_m: float,
    total_weight_kn: float,
    member_count: int,
    base_shear_kn: float = 0,
) -> tuple[float, float, float]:
    """
    Estimate member demand (axial, bending, shear) in kN.
    
    Simplified distribution:
    - Columns: primarily axial (weight + roof)
    - Beams: primarily bending (distributed load)
    - Braces: primarily axial (lateral load)
    - Rafters: combined bending + axial
    """
    weight_per_member = total_weight_kn / max(member_count, 1)
    lateral_per_member = base_shear_kn / max(member_count, 1)

    if member_type in ("column",):
        axial = weight_per_member * 1.2  # gravity + load factor
        bending = lateral_per_member * 0.5
        shear = lateral_per_member * 0.3
    elif member_type in ("beam",):
        axial = weight_per_member * 0.1
        bending = weight_per_member * 1.5  # distributed load moment
        shear = weight_per_member * 0.8
    elif member_type in ("brace",):
        axial = lateral_per_member * 1.5  # lateral load resistance
        bending = lateral_per_member * 0.1
        shear = lateral_per_member * 0.2
    elif member_type in ("rafter",):
        axial = weight_per_member * 0.3
        bending = weight_per_member * 1.2
        shear = weight_per_member * 0.5
    else:
        axial = weight_per_member
        bending = weight_per_member * 0.5
        shear = weight_per_member * 0.3

    return axial, bending, shear


# -------------------------------------------------------------------
# Main calculation
# -------------------------------------------------------------------

def calculate_safety_factors(
    members: list[dict[str, Any]],
    total_weight_kn: float = 10.0,
    base_shear_kn: float = 0.0,
) -> SafetyFactorReport:
    """
    Calculate safety factors for all members in a design.

    Args:
        members: List of member dicts with id, type, material_id, length_m, diameter_m.
        total_weight_kn: Total building weight for load distribution.
        base_shear_kn: Total base shear for lateral load distribution.

    Returns:
        SafetyFactorReport with per-member and overall results.
    """
    results: list[MemberSafetyResult] = []

    for mem in members:
        mat_type = mem.get("material_id", "treated_bamboo")
        mat = MATERIAL_CATALOG.get(mat_type)
        if mat is None:
            continue

        length = mem.get("length_m", 3.0)
        diameter = mem.get("diameter_m", 0.10)  # default 100mm

        # Capacity
        axial_cap = _axial_capacity(mat, diameter)
        bending_cap = _bending_capacity(mat, diameter, length)
        shear_cap = _shear_capacity(mat, diameter)

        # Demand
        axial_dem, bending_dem, shear_dem = _estimate_demand(
            mem.get("type", "beam"), length, total_weight_kn,
            len(members), base_shear_kn,
        )

        # Safety factors (demand / capacity is utilization; SF = 1/utilization = cap/demand)
        axial_sf = axial_cap / max(axial_dem, 0.001)
        bending_sf = bending_cap / max(bending_dem, 0.001)
        shear_sf = shear_cap / max(shear_dem, 0.001)

        # Governing (minimum) safety factor
        governing = min(axial_sf, bending_sf, shear_sf)
        if governing == axial_sf:
            mode = "axial"
        elif governing == bending_sf:
            mode = "bending"
        else:
            mode = "shear"

        is_safe = governing >= 1.5

        if governing >= 3.0:
            assessment = "HIGHLY ADEQUATE — substantial reserve capacity"
        elif governing >= 2.0:
            assessment = "ADEQUATE — good safety margin"
        elif governing >= 1.5:
            assessment = "MINIMUM ACCEPTABLE — meets humanitarian standard"
        elif governing >= 1.0:
            assessment = "MARGINAL — below recommended safety factor"
        else:
            assessment = "INADEQUATE — member likely to fail under load"

        results.append(MemberSafetyResult(
            member_id=mem.get("id", "unknown"),
            member_type=mem.get("type", "unknown"),
            material_type=mat_type,
            length_m=length,
            diameter_m=diameter,
            axial_capacity_kn=axial_cap,
            bending_capacity_kn=bending_cap,
            shear_capacity_kn=shear_cap,
            axial_demand_kn=axial_dem,
            bending_demand_kn=bending_dem,
            shear_demand_kn=shear_dem,
            axial_sf=axial_sf,
            bending_sf=bending_sf,
            shear_sf=shear_sf,
            governing_sf=governing,
            governing_mode=mode,
            is_safe=is_safe,
            assessment=assessment,
        ))

    # Overall
    if results:
        min_sf = min(r.governing_sf for r in results)
        avg_sf = sum(r.governing_sf for r in results) / len(results)
        safe_count = sum(1 for r in results if r.is_safe)
    else:
        min_sf = 0.0
        avg_sf = 0.0
        safe_count = 0

    unsafe_count = len(results) - safe_count

    if unsafe_count == 0:
        overall = "ALL MEMBERS SAFE — design meets structural requirements"
    elif unsafe_count <= len(results) * 0.2:
        overall = f"{unsafe_count} member(s) below safety threshold — review and reinforce"
    else:
        overall = f"SIGNIFICANT SAFETY CONCERNS — {unsafe_count}/{len(results)} members below threshold"

    return SafetyFactorReport(
        members=results,
        overall_min_sf=min_sf,
        overall_avg_sf=avg_sf,
        members_safe=safe_count,
        members_unsafe=unsafe_count,
        total_members=len(results),
        overall_assessment=overall,
    )
