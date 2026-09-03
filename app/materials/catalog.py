"""
Panah Material Property Catalog.

Provides reference engineering properties (density, elastic modulus,
allowable stress, expected lifespan) for the material types used in a
ConstraintSet / DesignMember.

Design principles
------------------
1. Values here are typical/reference figures used for structural
   prescreening. They are NOT lab-certified test data for a specific
   material batch and must never be presented as such.
2. Every property carries a `source` string so the UI can disclose that
   this is a reference/simplified value, matching the caution already
   expressed in app/rules.py.
3. Lookup is by material *type* (e.g. "treated_bamboo"), since a
   ConstraintSet's MaterialConstraint.type is the durable classification;
   individual material_id values (e.g. "MAT-BAM-01") are project-specific
   instances of a type.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialProperties:
    """Reference structural properties for one material type."""

    type: str
    display_name: str
    density_kg_m3: float
    elastic_modulus_pa: float
    allowable_bending_stress_pa: float
    allowable_axial_stress_pa: float
    expected_lifespan_years: float
    hollow_section_factor: float
    source: str
    # Pricing (USD) — reference regional estimates for Pakistan/South Asia
    unit_cost_usd: float = 0.0
    cost_unit: str = "per piece"
    local_availability: str = "available"  # available / limited / imported


# ---------------------------------------------------------------------------
# Reference catalog
# ---------------------------------------------------------------------------
# hollow_section_factor approximates the reduction in moment of inertia for
# naturally hollow members (e.g. bamboo culms) versus a solid circular
# cross-section of the same outer diameter. 1.0 = treated as solid.

MATERIAL_CATALOG: dict[str, MaterialProperties] = {
    "treated_bamboo": MaterialProperties(
        type="treated_bamboo",
        display_name="Treated Bamboo",
        density_kg_m3=600.0,
        elastic_modulus_pa=10.0e9,
        allowable_bending_stress_pa=8.0e6,
        allowable_axial_stress_pa=6.0e6,
        expected_lifespan_years=15.0,
        hollow_section_factor=0.6,
        source="Typical treated structural bamboo (Guadua-type), reference range for prescreening only.",
        unit_cost_usd=3.50,
        cost_unit="per 3m pole",
        local_availability="available",
    ),
    "reclaimed_timber": MaterialProperties(
        type="reclaimed_timber",
        display_name="Reclaimed Timber",
        density_kg_m3=600.0,
        elastic_modulus_pa=11.0e9,
        allowable_bending_stress_pa=12.0e6,
        allowable_axial_stress_pa=9.0e6,
        expected_lifespan_years=20.0,
        hollow_section_factor=1.0,
        source="Typical softwood/reclaimed timber reference range for prescreening only.",
        unit_cost_usd=5.00,
        cost_unit="per 2.5m plank",
        local_availability="available",
    ),
    "stabilized_mud_brick": MaterialProperties(
        type="stabilized_mud_brick",
        display_name="Stabilized Mud-Brick (CSEB)",
        density_kg_m3=1800.0,
        elastic_modulus_pa=2.0e9,
        allowable_bending_stress_pa=1.0e6,
        allowable_axial_stress_pa=5.5e6,
        expected_lifespan_years=20.0,
        hollow_section_factor=1.0,
        source="Cement-stabilized earth block, typical compressive reference ~5.5 MPa.",
        unit_cost_usd=0.80,
        cost_unit="per brick",
        local_availability="available",
    ),
    "corrugated_tin": MaterialProperties(
        type="corrugated_tin",
        display_name="Corrugated Tin (Roofing)",
        density_kg_m3=7850.0,
        elastic_modulus_pa=200.0e9,
        allowable_bending_stress_pa=150.0e6,
        allowable_axial_stress_pa=100.0e6,
        expected_lifespan_years=8.0,
        hollow_section_factor=1.0,
        source="Light-gauge galvanized steel roofing sheet, cladding only (not a primary structural member).",
        unit_cost_usd=12.00,
        cost_unit="per sheet",
        local_availability="limited",
    ),
    "steel_connector": MaterialProperties(
        type="steel_connector",
        display_name="Steel Connector Hardware",
        density_kg_m3=7850.0,
        elastic_modulus_pa=200.0e9,
        allowable_bending_stress_pa=200.0e6,
        allowable_axial_stress_pa=150.0e6,
        expected_lifespan_years=25.0,
        hollow_section_factor=1.0,
        source="Mild steel fixings/hardware reference values.",
        unit_cost_usd=1.50,
        cost_unit="per connector",
        local_availability="imported",
    ),
}


def get_material_properties(material_type: str) -> MaterialProperties | None:
    """Look up reference structural properties for a material type.

    Returns None for unknown types so callers can degrade to
    NOT_EVALUATED instead of guessing.
    """
    return MATERIAL_CATALOG.get(material_type)
