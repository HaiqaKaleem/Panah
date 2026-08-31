"""
Panah Simplified Structural Analysis Engine.

Computes engineering-based (but deliberately simplified) structural
figures from a ConstraintSet and a list of canonical DesignMembers:

- self-weight / dead load
- governing beam deflection under a uniform load, vs an allowable limit
- live/snow load capacity derived from bending + deflection limits
- lateral wind force vs available cross-brace capacity
- an overall integrity score summarizing the worst-case utilization

Design principles
------------------
1. This is a *prescreening* engine, not a certified structural design
   tool. Every simplifying assumption is named as a constant below so
   it is auditable, not buried in arithmetic.
2. Circular solid-beam mechanics are used throughout (bending/deflection
   of a simply supported beam under a uniform distributed load). Members
   without a diameter cannot be analyzed and are skipped, not guessed.
3. This module produces evidence. It does not decide PASS/FAIL by itself
   for Sphere rules — that remains app/rules.py's responsibility, this
   module only supplies the numbers rules.py was previously missing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.constraints.schemas import ConstraintSet
from app.materials.catalog import MaterialProperties, get_material_properties
from app.schemas.design_version import DesignMember

# ---------------------------------------------------------------------------
# Named simplifying assumptions (kept explicit and adjustable)
# ---------------------------------------------------------------------------

GRAVITY_M_S2 = 9.81
AIR_DENSITY_KG_M3 = 1.225
WIND_DRAG_COEFFICIENT = 1.3
ASSUMED_WALL_HEIGHT_M = 2.4  # used when a design version height is unavailable
ASSUMED_MEMBER_SPACING_M = 1.0  # rafter/truss tributary spacing
DEFLECTION_LIMIT_RATIO = 240  # allowable deflection = span / 240
REQUIRED_WIND_KMH = 120.0  # mirrors SPHERE-TECH-WIND-001
REQUIRED_SNOW_KG_M2 = 50.0  # mirrors SPHERE-TECH-SNOW-001
REQUIRED_LIFESPAN_MONTHS = 6.0  # mirrors SPHERE-TECH-LIFE-001

LOAD_BEARING_TYPES = {"beam", "rafter", "column"}
BRACE_TYPES = {"brace"}


@dataclass(frozen=True)
class DeflectionPoint:
    x_m: float
    deflection_mm: float


@dataclass(frozen=True)
class StructuralAnalysisResult:
    analyzable: bool
    reason: str | None

    governing_member_id: str | None = None
    span_m: float | None = None

    dead_load_kg: float = 0.0
    live_load_capacity_kg_m2: float | None = None
    max_deflection_mm: float | None = None
    allowable_deflection_mm: float | None = None
    deflection_curve: list[DeflectionPoint] = field(default_factory=list)

    wind_capacity_kmh: float | None = None
    wind_demand_n: float | None = None
    wind_capacity_n: float | None = None
    bracing_present: bool = False

    lifespan_months: float | None = None

    overall_integrity_score: float | None = None
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "analyzable": self.analyzable,
            "reason": self.reason,
            "governing_member_id": self.governing_member_id,
            "span_m": self.span_m,
            "dead_load_kg": round(self.dead_load_kg, 1),
            "live_load_capacity_kg_m2": (
                round(self.live_load_capacity_kg_m2, 1)
                if self.live_load_capacity_kg_m2 is not None
                else None
            ),
            "max_deflection_mm": (
                round(self.max_deflection_mm, 1)
                if self.max_deflection_mm is not None
                else None
            ),
            "allowable_deflection_mm": (
                round(self.allowable_deflection_mm, 1)
                if self.allowable_deflection_mm is not None
                else None
            ),
            "deflection_curve": [
                {"x_m": round(p.x_m, 2), "deflection_mm": round(p.deflection_mm, 2)}
                for p in self.deflection_curve
            ],
            "wind_capacity_kmh": (
                round(self.wind_capacity_kmh, 1)
                if self.wind_capacity_kmh is not None
                else None
            ),
            "bracing_present": self.bracing_present,
            "lifespan_months": self.lifespan_months,
            "overall_integrity_score": self.overall_integrity_score,
            "assumptions": self.assumptions,
        }


def _circular_section(diameter_m: float, hollow_factor: float) -> tuple[float, float]:
    """Return (area_m2, moment_of_inertia_m4) for a circular section.

    hollow_factor scales the solid-section values down to approximate a
    naturally hollow member (e.g. a bamboo culm) of the same outer
    diameter. 1.0 leaves the solid-section values unchanged.
    """
    area = math.pi * (diameter_m**2) / 4.0
    inertia = math.pi * (diameter_m**4) / 64.0
    return area * hollow_factor, inertia * hollow_factor


def _material_lookup(constraints: ConstraintSet) -> dict[str, MaterialProperties]:
    """Map each project material_id to its catalog properties (if known)."""
    lookup: dict[str, MaterialProperties] = {}
    for material in constraints.materials:
        props = get_material_properties(material.type)
        if props is not None:
            lookup[material.id] = props
    return lookup


def analyze_structure(
    constraints: ConstraintSet,
    members: list[DesignMember],
    design_height_m: float | None = None,
) -> StructuralAnalysisResult:
    """Run the simplified structural analysis for one design."""

    assumptions = [
        f"Simply supported beam under uniform load; solid/hollow circular section.",
        f"Allowable deflection = span / {DEFLECTION_LIMIT_RATIO}.",
        f"Assumed rafter/truss spacing of {ASSUMED_MEMBER_SPACING_M} m for areal load conversion.",
        f"Assumed wall height of {design_height_m or ASSUMED_WALL_HEIGHT_M} m for wind force calculation.",
        "Reference material properties only — not certified test data for a specific batch.",
    ]

    material_props = _material_lookup(constraints)

    dead_load_kg = 0.0
    load_bearing_candidates: list[tuple[DesignMember, MaterialProperties, float, float]] = []
    brace_capacity_n = 0.0
    bracing_present = False
    lifespans_years: list[float] = []

    for member in members:
        props = material_props.get(member.material_id)
        if props is None or member.diameter_m is None or member.length_m is None:
            continue

        area_m2, inertia_m4 = _circular_section(member.diameter_m, props.hollow_section_factor)
        volume_m3 = area_m2 * member.length_m
        dead_load_kg += volume_m3 * props.density_kg_m3
        lifespans_years.append(props.expected_lifespan_years)

        if member.type in LOAD_BEARING_TYPES:
            load_bearing_candidates.append((member, props, area_m2, inertia_m4))

        if member.type in BRACE_TYPES:
            bracing_present = True
            brace_capacity_n += props.allowable_axial_stress_pa * area_m2

    if not load_bearing_candidates:
        return StructuralAnalysisResult(
            analyzable=False,
            reason="No load-bearing member has both a known material type and a diameter; cannot run analysis.",
            dead_load_kg=dead_load_kg,
            assumptions=assumptions,
        )

    # Governing member = longest span load-bearing member (worst case).
    governing_member, props, area_m2, inertia_m4 = max(
        load_bearing_candidates, key=lambda item: item[0].length_m or 0.0
    )
    span_m = governing_member.length_m or 0.0
    diameter_m = governing_member.diameter_m or 0.0

    allowable_deflection_m = span_m / DEFLECTION_LIMIT_RATIO

    # Governing distributed load capacity (N/m) from deflection and bending limits.
    w_deflection_limit = (
        (allowable_deflection_m * 384 * props.elastic_modulus_pa * inertia_m4)
        / (5 * span_m**4)
        if span_m > 0
        else 0.0
    )
    allowable_moment_n_m = (
        props.allowable_bending_stress_pa * inertia_m4 / (diameter_m / 2)
        if diameter_m > 0
        else 0.0
    )
    w_bending_limit = (8 * allowable_moment_n_m) / (span_m**2) if span_m > 0 else 0.0

    w_capacity_n_per_m = min(w_deflection_limit, w_bending_limit)

    self_weight_n_per_m = area_m2 * props.density_kg_m3 * GRAVITY_M_S2
    w_live_n_per_m = max(w_capacity_n_per_m - self_weight_n_per_m, 0.0)

    live_load_capacity_kg_m2 = (
        (w_live_n_per_m / ASSUMED_MEMBER_SPACING_M) / GRAVITY_M_S2
    )

    # Deflection curve for the governing beam under its capacity load.
    curve: list[DeflectionPoint] = []
    max_deflection_mm = 0.0
    samples = 9
    if span_m > 0 and props.elastic_modulus_pa > 0 and inertia_m4 > 0:
        for i in range(samples + 1):
            x = span_m * i / samples
            y_m = (w_capacity_n_per_m / (24 * props.elastic_modulus_pa * inertia_m4)) * (
                x**4 - 2 * span_m * x**3 + (span_m**3) * x
            )
            y_mm = abs(y_m) * 1000
            curve.append(DeflectionPoint(x_m=x, deflection_mm=y_mm))
            max_deflection_mm = max(max_deflection_mm, y_mm)

    # Wind check.
    wall_height_m = design_height_m or ASSUMED_WALL_HEIGHT_M
    wall_length_m = constraints.site.length_m
    required_wind_ms = REQUIRED_WIND_KMH * 1000 / 3600
    required_wind_pressure_pa = 0.5 * AIR_DENSITY_KG_M3 * required_wind_ms**2
    wind_demand_n = required_wind_pressure_pa * WIND_DRAG_COEFFICIENT * wall_height_m * wall_length_m

    if brace_capacity_n > 0:
        capacity_pressure_pa = brace_capacity_n / (WIND_DRAG_COEFFICIENT * wall_height_m * wall_length_m)
        capacity_ms = math.sqrt(max(2 * capacity_pressure_pa / AIR_DENSITY_KG_M3, 0.0))
        wind_capacity_kmh = capacity_ms * 3.6
    else:
        wind_capacity_kmh = 0.0

    # Lifespan (months), governed by the shortest-lived material actually used.
    lifespan_months = (min(lifespans_years) * 12) if lifespans_years else None

    # Overall integrity score: worst-case utilization across wind and snow checks.
    utilizations = []
    if brace_capacity_n > 0:
        utilizations.append(wind_demand_n / brace_capacity_n)
    else:
        utilizations.append(float("inf"))

    if live_load_capacity_kg_m2 > 0:
        utilizations.append(REQUIRED_SNOW_KG_M2 / live_load_capacity_kg_m2)
    else:
        utilizations.append(float("inf"))

    governing_utilization = max(utilizations)
    if math.isinf(governing_utilization) or governing_utilization <= 0:
        overall_integrity_score = 0.0
    else:
        overall_integrity_score = round(min(100.0, 100.0 / governing_utilization), 1)

    return StructuralAnalysisResult(
        analyzable=True,
        reason=None,
        governing_member_id=governing_member.id,
        span_m=span_m,
        dead_load_kg=dead_load_kg,
        live_load_capacity_kg_m2=live_load_capacity_kg_m2,
        max_deflection_mm=max_deflection_mm,
        allowable_deflection_mm=allowable_deflection_m * 1000,
        deflection_curve=curve,
        wind_capacity_kmh=wind_capacity_kmh,
        wind_demand_n=wind_demand_n,
        wind_capacity_n=brace_capacity_n,
        bracing_present=bracing_present,
        lifespan_months=lifespan_months,
        overall_integrity_score=overall_integrity_score,
        assumptions=assumptions,
    )
