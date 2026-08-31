"""
Cost Estimation Engine — Detailed Breakdown for Humanitarian Shelters

Provides realistic cost estimates including:
  - Material costs (from catalog)
  - Labor costs (by skill level and region)
  - Transport costs (distance-based)
  - Equipment rental
  - Contingencies (10-15%)
  - Waste factor (5-10%)

References:
  - OpenConstructionERP cost estimation methodology
  - Sphere Handbook economic sustainability guidelines
  - Pakistan/South Asia construction labor rates 2024-2025
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.materials.catalog import MATERIAL_CATALOG


# -------------------------------------------------------------------
# Reference data
# -------------------------------------------------------------------

LABOR_RATES_BY_REGION: dict[str, dict[str, float]] = {
    # skill_level: hourly_rate_usd
    "south_asia": {"unskilled": 1.50, "semi_skilled": 3.00, "skilled": 5.00, "supervisor": 8.00},
    "east_africa": {"unskilled": 1.20, "semi_skilled": 2.50, "skilled": 4.50, "supervisor": 7.00},
    "west_africa": {"unskilled": 1.00, "semi_skilled": 2.00, "skilled": 4.00, "supervisor": 6.50},
    "central_asia": {"unskilled": 1.80, "semi_skilled": 3.50, "skilled": 6.00, "supervisor": 9.00},
    "southeast_asia": {"unskilled": 2.00, "semi_skilled": 4.00, "skilled": 7.00, "supervisor": 10.00},
    "default": {"unskilled": 1.50, "semi_skilled": 3.00, "skilled": 5.50, "supervisor": 8.50},
}

# Construction time estimates (hours per shelter by complexity)
CONSTRUCTION_HOURS: dict[str, dict[str, float]] = {
    # shelter_type: {unskilled_hours, semi_skilled_hours, skilled_hours, supervisor_hours}
    "basic_tent": {"unskilled": 8, "semi_skilled": 4, "skilled": 2, "supervisor": 1},
    "bamboo_truss": {"unskilled": 40, "semi_skilled": 20, "skilled": 16, "supervisor": 4},
    "timber_frame": {"unskilled": 60, "semi_skilled": 30, "skilled": 24, "supervisor": 6},
    "mud_brick": {"unskilled": 80, "semi_skilled": 40, "skilled": 16, "supervisor": 8},
    "composite": {"unskilled": 50, "semi_skilled": 25, "skilled": 20, "supervisor": 5},
}

TRANSPORT_COST_PER_KM: dict[str, float] = {
    "truck": 0.50,      # USD per km (flatbed)
    "pickup": 0.30,     # USD per km
    "bicycle_cart": 0.05,
    "manual": 0.00,
}

WASTE_FACTOR = 0.08  # 8% material waste
CONTINGENCY_RATE = 0.12  # 12% contingency


# -------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------

@dataclass
class CostLineItem:
    """Single line item in cost estimate."""
    category: str  # "material", "labor", "transport", "equipment", "contingency"
    description: str
    quantity: float
    unit: str
    unit_cost_usd: float
    total_cost_usd: float
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "quantity": round(self.quantity, 2),
            "unit": self.unit,
            "unit_cost_usd": round(self.unit_cost_usd, 2),
            "total_cost_usd": round(self.total_cost_usd, 2),
            "notes": self.notes,
        }


@dataclass
class CostSummary:
    """Aggregated cost summary."""
    material_cost_usd: float
    labor_cost_usd: float
    transport_cost_usd: float
    equipment_cost_usd: float
    waste_cost_usd: float
    contingency_cost_usd: float
    subtotal_usd: float
    total_cost_usd: float
    cost_per_person_usd: float
    cost_per_m2_usd: float
    cost_per_m3_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_cost_usd": round(self.material_cost_usd, 2),
            "labor_cost_usd": round(self.labor_cost_usd, 2),
            "transport_cost_usd": round(self.transport_cost_usd, 2),
            "equipment_cost_usd": round(self.equipment_cost_usd, 2),
            "waste_cost_usd": round(self.waste_cost_usd, 2),
            "contingency_cost_usd": round(self.contingency_cost_usd, 2),
            "subtotal_usd": round(self.subtotal_usd, 2),
            "total_cost_usd": round(self.total_cost_usd, 2),
            "cost_per_person_usd": round(self.cost_per_person_usd, 2),
            "cost_per_m2_usd": round(self.cost_per_m2_usd, 2),
            "cost_per_m3_usd": round(self.cost_per_m3_usd, 2),
        }


@dataclass
class CostEstimationResult:
    """Complete cost estimation result."""
    line_items: list[CostLineItem]
    summary: CostSummary
    assumptions: list[str]
    region: str
    shelter_type: str
    occupancy: int
    floor_area_m2: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "line_items": [item.to_dict() for item in self.line_items],
            "summary": self.summary.to_dict(),
            "assumptions": self.assumptions,
            "region": self.region,
            "shelter_type": self.shelter_type,
            "occupancy": self.occupancy,
            "floor_area_m2": round(self.floor_area_m2, 2),
        }


# -------------------------------------------------------------------
# Estimation engine
# -------------------------------------------------------------------

def estimate_cost(
    materials: list[dict[str, Any]],
    region: str = "south_asia",
    shelter_type: str = "bamboo_truss",
    occupancy: int = 5,
    floor_area_m2: float = 20.0,
    transport_distance_km: float = 10.0,
    equipment_days: float = 0,
) -> CostEstimationResult:
    """
    Generate a detailed cost estimate for a shelter construction.

    Args:
        materials: List of {type, qty, unit_cost_usd, length_m} dicts.
        region: Geographic region for labor rates.
        shelter_type: Type of shelter for construction time estimates.
        occupancy: Number of people the shelter serves.
        floor_area_m2: Floor area in square meters.
        transport_distance_km: Distance to transport materials.
        equipment_days: Days of heavy equipment rental.

    Returns:
        CostEstimationResult with line items and summary.
    """
    line_items: list[CostLineItem] = []
    assumptions: list[str] = []

    # --- Material costs ---
    total_material_cost = 0.0
    for mat in materials:
        mat_type = mat.get("type", "unknown")
        qty = mat.get("qty", 1)
        unit_cost = mat.get("unit_cost_usd", 0)
        cat = MATERIAL_CATALOG.get(mat_type)
        notes = ""
        if cat:
            unit_cost = unit_cost or cat.unit_cost_usd
            notes = f"Reference: {cat.source[:80]}"

        item_cost = qty * unit_cost
        total_material_cost += item_cost

        line_items.append(CostLineItem(
            category="material",
            description=f"{mat_type.replace('_', ' ').title()} (qty: {qty})",
            quantity=qty,
            unit="pieces",
            unit_cost_usd=unit_cost,
            total_cost_usd=item_cost,
            notes=notes,
        ))

    # Waste factor
    waste_cost = total_material_cost * WASTE_FACTOR
    line_items.append(CostLineItem(
        category="material",
        description="Material waste allowance (8%)",
        quantity=1,
        unit="lump sum",
        unit_cost_usd=waste_cost,
        total_cost_usd=waste_cost,
        notes="Industry standard waste factor for cut-to-length materials",
    ))
    assumptions.append(f"Material waste factor: {WASTE_FACTOR * 100:.0f}%")

    # --- Labor costs ---
    labor_rates = LABOR_RATES_BY_REGION.get(region, LABOR_RATES_BY_REGION["default"])
    construction_hours = CONSTRUCTION_HOURS.get(shelter_type, CONSTRUCTION_HOURS["bamboo_truss"])
    total_labor_cost = 0.0

    for skill_level in ["unskilled", "semi_skilled", "skilled", "supervisor"]:
        hours = construction_hours.get(skill_level, 0)
        rate = labor_rates.get(skill_level, 0)
        cost = hours * rate
        total_labor_cost += cost

        if hours > 0:
            line_items.append(CostLineItem(
                category="labor",
                description=f"{skill_level.replace('_', ' ').title()} labor",
                quantity=hours,
                unit="hours",
                unit_cost_usd=rate,
                total_cost_usd=cost,
                notes=f"Rate for {region} region",
            ))

    assumptions.append(f"Labor rates based on {region} regional averages")
    assumptions.append(f"Construction time estimated for {shelter_type} shelter type")

    # --- Transport costs ---
    transport_rate = TRANSPORT_COST_PER_KM.get("truck", 0.50)
    total_weight = sum(mat.get("qty", 1) * 5.0 for mat in materials)  # rough 5kg per piece
    transport_cost = total_weight * transport_distance_km * transport_rate / 100  # per 100kg-km

    if transport_distance_km > 0:
        line_items.append(CostLineItem(
            category="transport",
            description=f"Material transport ({transport_distance_km:.0f} km)",
            quantity=transport_distance_km,
            unit="km",
            unit_cost_usd=transport_rate,
            total_cost_usd=transport_cost,
            notes=f"Estimated total weight: {total_weight:.0f} kg",
        ))
        assumptions.append(f"Transport distance: {transport_distance_km} km by truck")

    # --- Equipment costs ---
    equipment_daily_rate = 50.0  # USD/day for basic equipment
    equipment_cost = equipment_days * equipment_daily_rate

    if equipment_days > 0:
        line_items.append(CostLineItem(
            category="equipment",
            description=f"Equipment rental ({equipment_days:.0f} days)",
            quantity=equipment_days,
            unit="days",
            unit_cost_usd=equipment_daily_rate,
            total_cost_usd=equipment_cost,
            notes="Basic construction equipment (mixer, scaffolding)",
        ))

    # --- Subtotal and contingency ---
    subtotal = total_material_cost + waste_cost + total_labor_cost + transport_cost + equipment_cost
    contingency = subtotal * CONTINGENCY_RATE

    line_items.append(CostLineItem(
        category="contingency",
        description="Contingency allowance (12%)",
        quantity=1,
        unit="lump sum",
        unit_cost_usd=contingency,
        total_cost_usd=contingency,
        notes="Covers unforeseen conditions, price fluctuations, design changes",
    ))
    assumptions.append(f"Contingency: {CONTINGENCY_RATE * 100:.0f}% of subtotal")

    total = subtotal + contingency

    # --- Per-unit metrics ---
    cost_per_person = total / max(occupancy, 1)
    cost_per_m2 = total / max(floor_area_m2, 1.0)
    volume_m3 = floor_area_m2 * 2.5  # assume 2.5m avg height
    cost_per_m3 = total / max(volume_m3, 1.0)

    summary = CostSummary(
        material_cost_usd=total_material_cost + waste_cost,
        labor_cost_usd=total_labor_cost,
        transport_cost_usd=transport_cost,
        equipment_cost_usd=equipment_cost,
        waste_cost_usd=waste_cost,
        contingency_cost_usd=contingency,
        subtotal_usd=subtotal,
        total_cost_usd=total,
        cost_per_person_usd=cost_per_person,
        cost_per_m2_usd=cost_per_m2,
        cost_per_m3_usd=cost_per_m3,
    )

    return CostEstimationResult(
        line_items=line_items,
        summary=summary,
        assumptions=assumptions,
        region=region,
        shelter_type=shelter_type,
        occupancy=occupancy,
        floor_area_m2=floor_area_m2,
    )
