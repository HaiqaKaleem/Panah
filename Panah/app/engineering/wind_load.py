"""
Wind Load Engine — ASCE 7 Simplified Procedure for Low-Rise Shelters

Implements the envelope procedure from ASCE 7-22 Chapter 28 for
enclosed and partially enclosed low-rise buildings (mean roof height ≤ 18m).

Key formulas:
  qh = 0.613 × Kz × Kzt × Kd × V²  (velocity pressure, Pa)
  P = qh × (GCpf - GCpi)           (design wind pressure, Pa)

References:
  - ASCE 7-22 §28.3 (Envelope Procedure)
  - Sphere Handbook 24.1 §4.3 (Wind-resistant construction)
  - IRC 2021 §R301.2.1 (Wind design)

This module is deterministic — no LLM calls. All values are reference
figures for prescreening only, not a substitute for site-specific
engineering analysis.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExposureCategory(str, Enum):
    """ASCE 7 exposure categories (§26.7)."""
    B = "B"  # Urban/suburban, many obstructions
    C = "C"  # Open terrain, scattered obstructions
    D = "D"  # Flat, unobstructed, near water


class WindRiskCategory(str, Enum):
    """ASCE 7 risk categories (Table 1.5-1)."""
    I = "I"        # Temporary structures
    II = "II"      # Standard (most shelters)
    III = "III"    # Essential facilities
    IV = "IV"      # Critical facilities


class EnclosureClassification(str, Enum):
    ENCLOSED = "enclosed"
    PARTIALLY_ENCLOSED = "partially_enclosed"
    OPEN = "open"


# -------------------------------------------------------------------
# Reference data
# -------------------------------------------------------------------

# Basic wind speed by region (3-second gust, mph → m/s conversion)
# These are simplified reference values for humanitarian contexts
REGIONAL_WIND_SPEEDS_M_S: dict[str, float] = {
    "coastal_south_asia": 45.0,      # ~100 mph, cyclone-prone
    "interior_south_asia": 35.0,     # ~78 mph, moderate
    "central_asia": 30.0,            # ~67 mph, moderate
    "east_africa": 33.0,             # ~74 mph, moderate
    "west_africa": 30.0,             # ~67 mph
    "caribbean": 50.0,               # ~112 mph, hurricane-prone
    "southeast_asia": 40.0,          # ~89 mph, typhoon zone
    "middle_east": 35.0,             # ~78 mph
    "sahel": 30.0,                   # ~67 mph
}

# Kz coefficients by height and exposure (Table 26.10-1)
# Format: {height_m: {exposure: Kz}}
KZ_TABLE: dict[float, dict[str, float]] = {
    0.0: {"B": 0.57, "C": 0.85, "D": 1.03},
    1.0: {"B": 0.57, "C": 0.85, "D": 1.03},
    1.5: {"B": 0.62, "C": 0.90, "D": 1.08},
    2.0: {"B": 0.66, "C": 0.94, "D": 1.12},
    2.5: {"B": 0.70, "C": 0.98, "D": 1.16},
    3.0: {"B": 0.74, "C": 1.01, "D": 1.19},
    4.0: {"B": 0.79, "C": 1.06, "D": 1.23},
    5.0: {"B": 0.84, "C": 1.09, "D": 1.26},
    6.0: {"B": 0.88, "C": 1.12, "D": 1.29},
    8.0: {"B": 0.95, "C": 1.17, "D": 1.33},
    10.0: {"B": 1.00, "C": 1.22, "D": 1.36},
    15.0: {"B": 1.09, "C": 1.29, "D": 1.42},
}

# Topographic factor Kzt (Table 26.8-1) — simplified
KZT_FACTORS: dict[str, float] = {
    "flat": 1.0,
    "ridge": 1.6,
    "escarpment": 1.3,
    "hill": 1.2,
}

# Wind directionality factor Kd (Table 26.6-1)
KD_FACTORS: dict[str, float] = {
    "main_frame": 0.85,
    "mwfrs_low_rise": 0.85,
    "components": 0.90,
    "freestanding_walls": 0.90,
}

# External pressure coefficients GCpf for low-rise (Table 28.6-1)
# Effective wind area ≤ 9.29 m² (100 ft²)
GCPF_COEFFICIENTS: dict[str, dict[str, float]] = {
    # Zone: {wall_or_roof: coefficient}
    "zone_1_interior_wall": {"pressure": 0.40, "suction": -0.29},
    "zone_2_end_wall": {"pressure": 0.53, "suction": -0.43},
    "zone_3_corner_wall": {"pressure": 0.63, "suction": -0.53},
    "zone_4_interior_roof": {"pressure": -0.45, "suction": -0.65},
    "zone_5_edge_roof": {"pressure": -0.69, "suction": -0.89},
    "zone_6_corner_roof": {"pressure": -0.89, "suction": -1.09},
}

# Internal pressure coefficient GCpi (Table 26.13-1)
GCPI: dict[str, float] = {
    "enclosed": 0.18,
    "partially_enclosed": 0.55,
    "open": 0.00,
}


# -------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------

@dataclass
class WindLoadInput:
    """Input parameters for wind load calculation."""
    # Building geometry
    mean_roof_height_m: float
    plan_length_m: float
    plan_width_m: float
    roof_slope_deg: float = 0.0

    # Wind parameters
    basic_wind_speed_m_s: float | None = None  # None = auto from region
    region: str = "interior_south_asia"
    exposure_category: str = "C"
    risk_category: str = "II"
    enclosure_classification: str = "enclosed"
    topographic_factor: float = 1.0  # Kzt

    # Building parameters
    importance_factor: float = 1.0   # I (Table 1.5-2)
    directionality_factor: float = 0.85  # Kd


@dataclass
class WindPressureZone:
    """Wind pressure for one building zone."""
    zone_id: str
    zone_name: str
    surface_type: str  # "wall" or "roof"
    positive_pressure_pa: float
    negative_pressure_pa: float  # suction
    net_pressure_pa: float  # worst case


@dataclass
class WindLoadResult:
    """Complete wind load calculation result."""
    # Velocity pressure
    velocity_pressure_pa: float
    kz: float
    kz_factor: float
    kd: float
    wind_speed_m_s: float
    gust_effect_factor: float

    # Design pressures
    gcpi: float
    max_positive_pressure_pa: float
    max_negative_pressure_pa: float

    # Per-zone results
    zones: list[WindPressureZone]

    # Summary
    governing_pressure_pa: float
    governing_zone: str
    governing_case: str

    # Safety assessment
    is_wind_resistant: bool
    safety_margin: float  # ratio of capacity / demand
    assessment: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "velocity_pressure_pa": round(self.velocity_pressure_pa, 2),
            "velocity_pressure_kpa": round(self.velocity_pressure_pa / 1000, 3),
            "coefficients": {
                "kz": round(self.kz, 3),
                "kzt": round(self.kz_factor, 3),
                "kd": round(self.kd, 3),
                "gcpi": round(self.gcpi, 3),
                "gust_effect_factor": round(self.gust_effect_factor, 3),
            },
            "wind_speed_m_s": round(self.wind_speed_m_s, 1),
            "wind_speed_kmh": round(self.wind_speed_m_s * 3.6, 1),
            "max_positive_pressure_pa": round(self.max_positive_pressure_pa, 2),
            "max_negative_pressure_pa": round(self.max_negative_pressure_pa, 2),
            "max_positive_pressure_kpa": round(self.max_positive_pressure_pa / 1000, 3),
            "max_negative_pressure_kpa": round(self.max_negative_pressure_pa / 1000, 3),
            "zones": [
                {
                    "zone_id": z.zone_id,
                    "zone_name": z.zone_name,
                    "surface": z.surface_type,
                    "positive_pa": round(z.positive_pressure_pa, 2),
                    "negative_pa": round(z.negative_pressure_pa, 2),
                    "net_pa": round(z.net_pressure_pa, 2),
                }
                for z in self.zones
            ],
            "governing_pressure_pa": round(self.governing_pressure_pa, 2),
            "governing_pressure_kpa": round(self.governing_pressure_pa / 1000, 3),
            "governing_zone": self.governing_zone,
            "governing_case": self.governing_case,
            "safety_assessment": {
                "is_wind_resistant": self.is_wind_resistant,
                "safety_margin": round(self.safety_margin, 2),
                "assessment": self.assessment,
            },
            "reference": "ASCE 7-22 §28.3 Envelope Procedure (simplified for prescreening)",
        }


# -------------------------------------------------------------------
# Calculation engine
# -------------------------------------------------------------------

def _interpolate_kz(height_m: float, exposure: str) -> float:
    """Interpolate Kz from the table for a given height."""
    heights = sorted(KZ_TABLE.keys())
    if height_m <= heights[0]:
        return KZ_TABLE[heights[0]][exposure]
    if height_m >= heights[-1]:
        return KZ_TABLE[heights[-1]][exposure]

    for i in range(len(heights) - 1):
        h0, h1 = heights[i], heights[i + 1]
        if h0 <= height_m <= h1:
            frac = (height_m - h0) / (h1 - h0)
            kz0 = KZ_TABLE[h0][exposure]
            kz1 = KZ_TABLE[h1][exposure]
            return kz0 + frac * (kz1 - kz0)
    return KZ_TABLE[heights[-1]][exposure]


def _gust_effect_factor(height_m: float) -> float:
    """Simplified gust effect factor G for rigid structures (§26.11).
    
    For shelters (fundamental frequency > 1 Hz), G = 0.85 is typical.
    For more flexible structures, G can be higher.
    """
    # Fundamental frequency approximation (simplified)
    # f = 1 / (0.0724 * H^0.8) for cantilever structures
    f = 1.0 / (0.0724 * max(height_m, 1.0) ** 0.8)
    if f >= 1.0:
        return 0.85  # Rigid structure
    # Flexible structure — higher gust factor
    return 0.85 + 0.15 * (1.0 - f)


def calculate_wind_loads(inp: WindLoadInput) -> WindLoadResult:
    """
    Calculate wind loads per ASCE 7-22 §28.3 Envelope Procedure.

    Args:
        inp: WindLoadInput with building geometry and wind parameters.

    Returns:
        WindLoadResult with per-zone pressures and safety assessment.
    """
    # 1. Determine basic wind speed
    if inp.basic_wind_speed_m_s is not None:
        V = inp.basic_wind_speed_m_s
    else:
        V = REGIONAL_WIND_SPEEDS_M_S.get(inp.region, 35.0)

    # 2. Velocity pressure coefficient Kz (Table 26.10-1)
    kz = _interpolate_kz(inp.mean_roof_height_m, inp.exposure_category)

    # 3. Velocity pressure: qh = 0.613 × Kz × Kzt × Kd × V²
    qh = 0.613 * kz * inp.topographic_factor * inp.directionality_factor * V ** 2

    # 4. Gust effect factor
    G = _gust_effect_factor(inp.mean_roof_height_m)

    # 5. Internal pressure coefficient
    gcpi = GCPI.get(inp.enclosure_classification, 0.18)

    # 6. Calculate per-zone pressures
    zones: list[WindPressureZone] = []
    max_positive = 0.0
    max_negative = 0.0
    governing_zone = ""
    governing_case = ""
    governing_pressure = 0.0

    zone_definitions = [
        ("zone_1", "Interior Wall", "wall"),
        ("zone_2", "End Wall", "wall"),
        ("zone_3", "Corner Wall", "wall"),
        ("zone_4", "Interior Roof", "roof"),
        ("zone_5", "Edge Roof", "roof"),
        ("zone_6", "Corner Roof", "roof"),
    ]

    for zone_id, zone_name, surface_type in zone_definitions:
        coeffs = GCPF_COEFFICIENTS.get(zone_id, GCPF_COEFFICIENTS["zone_1_interior_wall"])

        # P = qh × G × (GCpf - GCpi)
        pos = qh * G * (coeffs["pressure"] - gcpi)
        neg = qh * G * (coeffs["suction"] - gcpi)

        # Net pressure (worst case = max absolute)
        net = min(pos, neg)  # most negative (suction governs for lightweight)

        zones.append(WindPressureZone(
            zone_id=zone_id,
            zone_name=zone_name,
            surface_type=surface_type,
            positive_pressure_pa=pos,
            negative_pressure_pa=neg,
            net_pressure_pa=net,
        ))

        # Track governing pressure
        abs_pos = abs(pos)
        abs_neg = abs(neg)
        if abs_pos > abs(governing_pressure):
            governing_pressure = abs_pos
            governing_zone = zone_id
            governing_case = f"positive_{zone_name.lower().replace(' ', '_')}"
        if abs_neg > abs(governing_pressure):
            governing_pressure = abs_neg
            governing_zone = zone_id
            governing_case = f"negative_{zone_name.lower().replace(' ', '_')}"

        max_positive = max(max_positive, pos)
        max_negative = min(max_negative, neg)

    # 7. Safety assessment
    # For a lightweight shelter, typical connection capacity ~500-1000 Pa
    # This is a rough prescreening — real analysis needs member-level checks
    shelter_capacity_pa = 800.0  # Reference capacity for well-built shelter
    safety_margin = shelter_capacity_pa / max(governing_pressure, 1.0)

    is_wind_resistant = safety_margin >= 1.5  # Factor of safety = 1.5

    if safety_margin >= 2.0:
        assessment = "WELL DESIGNED — substantial safety margin against wind loads"
    elif safety_margin >= 1.5:
        assessment = "ADEQUATE — meets minimum safety factor of 1.5"
    elif safety_margin >= 1.0:
        assessment = "MARGINAL — below recommended safety factor, review recommended"
    else:
        assessment = "INADEQUATE — design does not resist wind loads, redesign required"

    return WindLoadResult(
        velocity_pressure_pa=qh,
        kz=kz,
        kz_factor=inp.topographic_factor,
        kd=inp.directionality_factor,
        wind_speed_m_s=V,
        gust_effect_factor=G,
        gcpi=gcpi,
        max_positive_pressure_pa=max_positive,
        max_negative_pressure_pa=max_negative,
        zones=zones,
        governing_pressure_pa=governing_pressure,
        governing_zone=governing_zone,
        governing_case=governing_case,
        is_wind_resistant=is_wind_resistant,
        safety_margin=safety_margin,
        assessment=assessment,
    )
