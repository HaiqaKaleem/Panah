"""
Seismic Load Calculator — Simplified Equivalent Lateral Force (ELF) Procedure

Implements ASCE 7-22 §12.8 equivalent lateral force method, adapted for
low-rise humanitarian shelters. Calculates base shear, vertical distribution,
and per-story lateral forces.

References:
  - ASCE 7-22 §12.8 (Equivalent Lateral Force Procedure)
  - IS 1893:2016 Part 1 (Indian seismic code — relevant for South Asia)
  - Sphere Handbook 24.1 §4.3 (Seismic-resistant construction)

This module is deterministic — no LLM calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SeismicDesignCategory(str, Enum):
    A = "A"  # Low seismic risk
    B = "B"
    C = "C"
    D = "D"  # High seismic risk
    E = "E"  # Very high seismic risk
    F = "F"  # Critical seismic risk


class SoilSiteClass(str, Enum):
    A = "A"  # Hard rock
    B = "B"  # Rock
    C = "C"  # Dense soil / soft rock
    D = "D"  # Stiff soil
    E = "E"  # Soft clay soil


# -------------------------------------------------------------------
# Reference data
# -------------------------------------------------------------------

# Seismic zone factors Z (IS 1893:2016 / simplified ASCE 7 Ss mapping)
SEISMIC_ZONE_FACTORS: dict[str, dict[str, float]] = {
    # region: {zone_factor_Z, mapped_sa_1s, mapped_sa_0p2s}
    "kashmir": {"z": 0.36, "ss": 1.50, "s1": 0.60},
    "northern_pakistan": {"z": 0.32, "ss": 1.25, "s1": 0.50},
    "islamabad": {"z": 0.24, "ss": 1.00, "s1": 0.40},
    "punjab": {"z": 0.16, "ss": 0.65, "s1": 0.25},
    "sindh": {"z": 0.20, "ss": 0.80, "s1": 0.32},
    "balochistan": {"z": 0.24, "ss": 1.00, "s1": 0.40},
    "khyber_pakhtunkhwa": {"z": 0.28, "ss": 1.10, "s1": 0.45},
    "east_africa_rift": {"z": 0.10, "ss": 0.50, "s1": 0.20},
    "hindu_kush": {"z": 0.36, "ss": 1.50, "s1": 0.60},
    "generic": {"z": 0.16, "ss": 0.65, "s1": 0.25},
}

# Site coefficients Fa and Fv (Tables 11.4-1 and 11.4-2, IS 1893)
SITE_COEFFICIENTS: dict[str, dict[str, float]] = {
    # Soil class: {Fa for various Ss ranges, Fv for various S1 ranges}
    "A": {"fa": 0.8, "fv": 0.8},
    "B": {"fa": 1.0, "fv": 1.0},
    "C": {"fa": 1.2, "fv": 1.5},
    "D": {"fa": 1.6, "fv": 2.4},
    "E": {"fa": 2.5, "fv": 3.5},
}

# Response modification factor R (Table 12.2-1, IS 1893)
# For shelters: typically light timber/bamboo = 3, masonry = 1.5
R_VALUES: dict[str, float] = {
    "timber_frame": 3.0,
    "bamboo_frame": 3.0,
    "light_steel": 3.5,
    "masonry_unreinforced": 1.5,
    "masonry_reinforced": 3.0,
    "concrete_frame": 5.0,
    "shell_structure": 3.0,
}


# -------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------

@dataclass
class SeismicLoadInput:
    """Input for seismic load calculation."""
    # Building
    total_height_m: float
    number_of_stories: int = 1
    structural_system: str = "bamboo_frame"

    # Seismic parameters
    region: str = "generic"
    seismic_zone_factor_z: float | None = None  # None = auto from region
    soil_site_class: str = "D"
    response_modification_r: float | None = None  # None = auto from system
    importance_factor: float = 1.0

    # Geometry
    plan_length_m: float = 5.0
    plan_width_m: float = 4.0

    # Story weights (for vertical distribution)
    story_weights_kn: list[float] | None = None  # None = uniform


@dataclass
class StoryForce:
    """Lateral force at one story level."""
    story_number: int
    height_m: float
    weight_kn: float
    vertical_distribution_factor: float
    lateral_force_kn: float
    shear_force_kn: float
    overturning_moment_knm: float


@dataclass
class SeismicLoadResult:
    """Complete seismic load calculation result."""
    # Parameters
    zone_factor_z: float
    spectral_acceleration_ss: float
    spectral_acceleration_s1: float
    site_coefficient_fa: float
    site_coefficient_fv: float
    design_spectral_acceleration_sds: float
    design_spectral_acceleration_sd1: float
    response_modification_r: float
    importance_factor: float
    approximate_period_t: float
    seismic_response_coefficient_cs: float

    # Results
    total_weight_kn: float
    base_shear_kn: float
    base_shear_coefficient: float

    # Per-story
    story_forces: list[StoryForce]

    # Summary
    max_lateral_force_kn: float
    max_overturning_moment_knm: float
    fundamental_period_s: float

    # Safety
    is_seismically_designed: bool
    safety_margin: float
    assessment: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameters": {
                "zone_factor_z": self.zone_factor_z,
                "spectral_acceleration_ss": round(self.spectral_acceleration_ss, 3),
                "spectral_acceleration_s1": round(self.spectral_acceleration_s1, 3),
                "site_coefficient_fa": self.site_coefficient_fa,
                "site_coefficient_fv": self.site_coefficient_fv,
                "design_sds": round(self.design_spectral_acceleration_sds, 3),
                "design_sd1": round(self.design_spectral_acceleration_sd1, 3),
                "response_modification_r": self.response_modification_r,
                "importance_factor": self.importance_factor,
                "fundamental_period_s": round(self.fundamental_period_s, 3),
                "seismic_response_coefficient_cs": round(self.seismic_response_coefficient_cs, 4),
            },
            "results": {
                "total_weight_kn": round(self.total_weight_kn, 2),
                "base_shear_kn": round(self.base_shear_kn, 2),
                "base_shear_coefficient": round(self.base_shear_coefficient, 4),
                "max_lateral_force_kn": round(self.max_lateral_force_kn, 2),
                "max_overturning_moment_knm": round(self.max_overturning_moment_knm, 2),
            },
            "story_forces": [
                {
                    "story": s.story_number,
                    "height_m": s.height_m,
                    "weight_kn": round(s.weight_kn, 2),
                    "distribution_factor": round(s.vertical_distribution_factor, 4),
                    "lateral_force_kn": round(s.lateral_force_kn, 2),
                    "shear_force_kn": round(s.shear_force_kn, 2),
                    "overturning_moment_knm": round(s.overturning_moment_knm, 2),
                }
                for s in self.story_forces
            ],
            "safety_assessment": {
                "is_seismically_designed": self.is_seismically_designed,
                "safety_margin": round(self.safety_margin, 2),
                "assessment": self.assessment,
            },
            "reference": "ASCE 7-22 §12.8 / IS 1893:2016 (simplified for prescreening)",
        }


# -------------------------------------------------------------------
# Calculation engine
# -------------------------------------------------------------------

def calculate_seismic_loads(inp: SeismicLoadInput) -> SeismicLoadResult:
    """
    Calculate seismic loads using equivalent lateral force procedure.

    Args:
        inp: SeismicLoadInput with building and seismic parameters.

    Returns:
        SeismicLoadResult with base shear, per-story forces, and safety assessment.
    """
    # 1. Seismic zone factor
    zone_data = SEISMIC_ZONE_FACTORS.get(inp.region, SEISMIC_ZONE_FACTORS["generic"])
    Z = inp.seismic_zone_factor_z if inp.seismic_zone_factor_z is not None else zone_data["z"]
    Ss = zone_data["ss"]
    S1 = zone_data["s1"]

    # 2. Site coefficients
    soil = SITE_COEFFICIENTS.get(inp.soil_site_class, SITE_COEFFICIENTS["D"])
    Fa = soil["fa"]
    Fv = soil["fv"]

    # 3. Design spectral acceleration
    Sds = (2.0 / 3.0) * Ss * Fa
    Sd1 = (2.0 / 3.0) * S1 * Fv

    # 4. Response modification factor
    R = inp.response_modification_r if inp.response_modification_r is not None else R_VALUES.get(inp.structural_system, 3.0)

    # 5. Fundamental period (approximate)
    # Ta = Ct × Hn^x (ASCE 7-22 Table 12.8-2)
    # For moment frames: Ct=0.0724, x=0.8
    # For other: Ct=0.0488, x=0.75
    Ct = 0.0488  # "other" — shelters are not moment frames
    x = 0.75
    Ta = Ct * inp.total_height_m ** x

    # 6. Seismic response coefficient
    # Cs = Sds / (R / Ie) but not less than Cs_min
    Cs = Sds / (R / inp.importance_factor)
    Cs_min = max(0.044 * Sds * inp.importance_factor, 0.01)
    Cs = max(Cs, Cs_min)

    # 7. Total building weight
    if inp.story_weights_kn and len(inp.story_weights_kn) == inp.number_of_stories:
        weights = inp.story_weights_kn
    else:
        # Estimate weight: ~2.5 kN/m² × floor area × number of stories
        floor_area = inp.plan_length_m * inp.plan_width_m
        unit_weight = 2.5  # kN/m² (lightweight shelter)
        story_weight = floor_area * unit_weight
        weights = [story_weight] * inp.number_of_stories

    total_weight = sum(weights)

    # 8. Base shear
    V = Cs * total_weight

    # 9. Vertical distribution (ASCE 7-22 §12.8.3)
    # Fi = V × (wi × hi^k) / Σ(wj × hj^k)
    # k = 1 for T ≤ 0.5s, k = 2 for T ≥ 2.5s, linear interpolation
    if Ta <= 0.5:
        k = 1.0
    elif Ta >= 2.5:
        k = 2.0
    else:
        k = 1.0 + 0.5 * (Ta - 0.5) / 2.0

    story_heights = []
    for i in range(inp.number_of_stories):
        if i == 0:
            story_heights.append(inp.total_height_m / inp.number_of_stories)
        else:
            story_heights.append(story_heights[-1] + inp.total_height_m / inp.number_of_stories)

    # Σ(wi × hi^k)
    sum_whk = sum(w * h ** k for w, h in zip(weights, story_heights))

    story_forces: list[StoryForce] = []
    cumulative_shear = V
    cumulative_moment = 0.0

    for i, (w, h) in enumerate(zip(weights, story_heights)):
        # Distribution factor
        dist_factor = (w * h ** k) / sum_whk if sum_whk > 0 else 0
        lateral_force = V * dist_factor

        # Story shear (cumulative from top)
        story_shear = sum(sf.lateral_force_kn for sf in story_forces[i:]) + lateral_force

        # Overturning moment
        moment = sum(sf.lateral_force_kn * (h - sf.height_m) for sf in story_forces) + lateral_force * 0
        cumulative_moment += lateral_force * h

        story_forces.append(StoryForce(
            story_number=i + 1,
            height_m=h,
            weight_kn=w,
            vertical_distribution_factor=dist_factor,
            lateral_force_kn=lateral_force,
            shear_force_kn=story_shear,
            overturning_moment_knm=cumulative_moment,
        ))

    # 10. Safety assessment
    # For lightweight shelters, typical lateral capacity ~0.15 × weight (R × Cs)
    capacity_coefficient = R * Cs / inp.importance_factor
    actual_demand = V / total_weight if total_weight > 0 else 0

    # Safety margin: how much reserve capacity exists
    # A well-designed shelter should have Cs demand well below capacity
    safety_margin = capacity_coefficient / max(actual_demand, 0.001)

    is_seismic = safety_margin >= 1.5

    if safety_margin >= 2.0:
        assessment = "WELL DESIGNED — substantial seismic resistance margin"
    elif safety_margin >= 1.5:
        assessment = "ADEQUATE — meets minimum seismic design criteria"
    elif safety_margin >= 1.0:
        assessment = "MARGINAL — below recommended margin, review needed"
    else:
        assessment = "INADEQUATE — design may not resist seismic forces"

    return SeismicLoadResult(
        zone_factor_z=Z,
        spectral_acceleration_ss=Ss,
        spectral_acceleration_s1=S1,
        site_coefficient_fa=Fa,
        site_coefficient_fv=Fv,
        design_spectral_acceleration_sds=Sds,
        design_spectral_acceleration_sd1=Sd1,
        response_modification_r=R,
        importance_factor=inp.importance_factor,
        approximate_period_t=Ta,
        seismic_response_coefficient_cs=Cs,
        total_weight_kn=total_weight,
        base_shear_kn=V,
        base_shear_coefficient=Cs,
        story_forces=story_forces,
        max_lateral_force_kn=max(sf.lateral_force_kn for sf in story_forces) if story_forces else 0,
        max_overturning_moment_knm=max(sf.overturning_moment_knm for sf in story_forces) if story_forces else 0,
        fundamental_period_s=Ta,
        is_seismically_designed=is_seismic,
        safety_margin=safety_margin,
        assessment=assessment,
    )
