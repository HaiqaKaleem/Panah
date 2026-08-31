"""
Project Templates — Pre-built constraint sets for common shelter types.

Templates encode best-practice constraint sets based on Sphere Handbook,
UNHCR specifications, and field-tested designs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProjectTemplate:
    """A reusable project template with pre-filled constraints."""
    template_id: str
    name: str
    description: str
    shelter_type: str
    occupancy_range: tuple[int, int]
    floor_area_range_m2: tuple[float, float]
    default_constraints: dict[str, Any]
    suggested_materials: list[dict[str, Any]]
    applicable_climates: list[str]
    estimated_cost_usd: float
    construction_days: int
    sphere_compliance: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "shelter_type": self.shelter_type,
            "occupancy_range": list(self.occupancy_range),
            "floor_area_range_m2": list(self.floor_area_range_m2),
            "default_constraints": self.default_constraints,
            "suggested_materials": self.suggested_materials,
            "applicable_climates": self.applicable_climates,
            "estimated_cost_usd": self.estimated_cost_usd,
            "construction_days": self.construction_days,
            "sphere_compliance": self.sphere_compliance,
        }


TEMPLATE_CATALOG: list[ProjectTemplate] = [
    ProjectTemplate(
        template_id="T-EMERGENCY-001",
        name="Emergency Family Shelter",
        description="Rapid-deployment emergency shelter for a family of 5-6. Assembled in under 4 hours with minimal tools.",
        shelter_type="emergency_tent",
        occupancy_range=(4, 6),
        floor_area_range_m2=(14.0, 20.0),
        default_constraints={
            "design_target": "emergency_shelter",
            "wind_resistance": "basic",
            "seismic_zone": "low",
        },
        suggested_materials=[
            {"type": "treated_bamboo", "qty": 20, "length_m": 3.0, "role": "frame poles"},
            {"type": "corrugated_tin", "qty": 8, "role": "roofing sheets"},
        ],
        applicable_climates=["semi_arid", "tropical", "temperate"],
        estimated_cost_usd=150.0,
        construction_days=1,
        sphere_compliance=["§4.1 Minimum Space", "§4.2 Structural Safety", "§4.3 Climate Protection"],
    ),
    ProjectTemplate(
        template_id="T-TRANSITIONAL-001",
        name="Transitional Bamboo Truss Shelter",
        description="Semi-permanent shelter with bamboo truss roof system. Designed for 2-5 year use period.",
        shelter_type="bamboo_truss",
        occupancy_range=(4, 8),
        floor_area_range_m2=(20.0, 35.0),
        default_constraints={
            "design_target": "transitional_shelter",
            "wind_resistance": "moderate",
            "seismic_zone": "moderate",
            "min_clearance_m": 2.2,
        },
        suggested_materials=[
            {"type": "treated_bamboo", "qty": 40, "length_m": 4.5, "role": "truss members"},
            {"type": "reclaimed_timber", "qty": 12, "length_m": 3.0, "role": "ridge and wall plates"},
            {"type": "corrugated_tin", "qty": 12, "role": "roofing"},
        ],
        applicable_climates=["semi_arid", "tropical", "temperate", "cold"],
        estimated_cost_usd=450.0,
        construction_days=3,
        sphere_compliance=["§4.1 Minimum Space", "§4.2 Structural Safety", "§4.3 Climate Protection", "§4.4 Water and Sanitation"],
    ),
    ProjectTemplate(
        template_id="T-DURABLE-001",
        name="Durable Timber Frame House",
        description="Permanent structure with timber frame and mud-brick walls. Designed for 15-20 year use.",
        shelter_type="timber_frame",
        occupancy_range=(5, 10),
        floor_area_range_m2=(30.0, 60.0),
        default_constraints={
            "design_target": "durable_housing",
            "wind_resistance": "high",
            "seismic_zone": "high",
            "min_clearance_m": 2.4,
        },
        suggested_materials=[
            {"type": "reclaimed_timber", "qty": 30, "length_m": 4.0, "role": "structural frame"},
            {"type": "stabilized_mud_brick", "qty": 500, "role": "wall infill"},
            {"type": "corrugated_tin", "qty": 20, "role": "roofing"},
            {"type": "steel_connector", "qty": 60, "role": "joint hardware"},
        ],
        applicable_climates=["semi_arid", "temperate", "cold"],
        estimated_cost_usd=2500.0,
        construction_days=14,
        sphere_compliance=["§4.1 Minimum Space", "§4.2 Structural Safety", "§4.3 Climate Protection", "§4.4 Water and Sanitation", "§4.5 Energy"],
    ),
    ProjectTemplate(
        template_id="T-COMMUNITY-001",
        name="Community Gathering Structure",
        description="Open-air community pavilion for meetings, education, and health services.",
        shelter_type="open_pavilion",
        occupancy_range=(20, 50),
        floor_area_range_m2=(60.0, 120.0),
        default_constraints={
            "design_target": "community_structure",
            "wind_resistance": "moderate",
            "seismic_zone": "moderate",
            "min_clearance_m": 2.8,
        },
        suggested_materials=[
            {"type": "treated_bamboo", "qty": 60, "length_m": 6.0, "role": "columns and trusses"},
            {"type": "reclaimed_timber", "qty": 20, "length_m": 5.0, "role": "ridge beams"},
            {"type": "corrugated_tin", "qty": 30, "role": "roofing"},
            {"type": "steel_connector", "qty": 80, "role": "joint hardware"},
        ],
        applicable_climates=["semi_arid", "tropical", "temperate"],
        estimated_cost_usd=3500.0,
        construction_days=10,
        sphere_compliance=["§4.1 Minimum Space", "§4.2 Structural Safety", "§4.3 Climate Protection"],
    ),
    ProjectTemplate(
        template_id="T-SCHOOL-001",
        name="Temporary Learning Space",
        description="Classroom shelter for 30-40 students. Optimized for ventilation and natural lighting.",
        shelter_type="classroom",
        occupancy_range=(30, 40),
        floor_area_range_m2=(50.0, 80.0),
        default_constraints={
            "design_target": "educational_structure",
            "wind_resistance": "moderate",
            "seismic_zone": "moderate",
            "min_clearance_m": 2.6,
            "natural_ventilation": True,
        },
        suggested_materials=[
            {"type": "treated_bamboo", "qty": 50, "length_m": 5.0, "role": "frame and trusses"},
            {"type": "stabilized_mud_brick", "qty": 300, "role": "half-walls"},
            {"type": "corrugated_tin", "qty": 25, "role": "roofing"},
        ],
        applicable_climates=["tropical", "semi_arid"],
        estimated_cost_usd=2000.0,
        construction_days=7,
        sphere_compliance=["§4.1 Minimum Space", "§4.2 Structural Safety", "§4.3 Climate Protection", "§4.6 Education"],
    ),
]


def list_templates() -> list[dict[str, Any]]:
    """Return all available project templates."""
    return [t.to_dict() for t in TEMPLATE_CATALOG]


def get_template(template_id: str) -> ProjectTemplate | None:
    """Get a specific template by ID."""
    for t in TEMPLATE_CATALOG:
        if t.template_id == template_id:
            return t
    return None


def get_templates_for_climate(climate: str) -> list[dict[str, Any]]:
    """Filter templates applicable to a given climate."""
    return [
        t.to_dict() for t in TEMPLATE_CATALOG
        if climate in t.applicable_climates
    ]
