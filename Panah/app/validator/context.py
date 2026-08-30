"""Validation context — bundles all inputs that deterministic rules need.

The validator never calls the LLM. Every rule receives a context
and returns a structured result. The context is built once per
validation run and shared across all rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.constraints.schemas import ConstraintSet
from app.materials.catalog import MaterialProperties, get_material_properties
from app.schemas.design_version import CanonicalDesignVersion
from app.structural.analysis import StructuralAnalysisResult


@dataclass
class ValidationContext:
    """All data needed by the deterministic validation engine."""

    design: CanonicalDesignVersion
    constraints: ConstraintSet
    analysis: StructuralAnalysisResult | None = None

    # Pre-computed lookups (populated by build_context)
    material_props: dict[str, MaterialProperties] = field(default_factory=dict)
    member_by_id: dict[str, Any] = field(default_factory=dict)
    connection_member_ids: set[str] = field(default_factory=set)
    connected_member_ids: set[str] = field(default_factory=set)

    rule_set_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize context for rule engine consumption."""
        return {
            "design": self.design.model_dump(),
            "constraints": self.constraints.model_dump(),
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "material_props": {
                k: {
                    "type": v.type,
                    "display_name": v.display_name,
                    "density_kg_m3": v.density_kg_m3,
                    "elastic_modulus_pa": v.elastic_modulus_pa,
                    "allowable_bending_stress_pa": v.allowable_bending_stress_pa,
                    "allowable_axial_stress_pa": v.allowable_axial_stress_pa,
                    "expected_lifespan_years": v.expected_lifespan_years,
                    "unit_cost_usd": v.unit_cost_usd,
                }
                for k, v in self.material_props.items()
            },
            "member_count": len(self.design.members),
            "connection_count": len(self.design.connections),
            "connected_member_count": len(self.connected_member_ids),
            "rule_set_version": self.rule_set_version,
        }


def build_context(
    design: CanonicalDesignVersion,
    constraints: ConstraintSet,
    analysis: StructuralAnalysisResult | None = None,
    rule_set_version: str = "1.0.0",
) -> ValidationContext:
    """Build a ValidationContext with pre-computed lookups."""
    material_props: dict[str, MaterialProperties] = {}
    for mat in constraints.materials:
        props = get_material_properties(mat.type)
        if props is not None:
            material_props[mat.id] = props

    member_by_id = {m.id: m for m in design.members}

    connection_member_ids: set[str] = set()
    connected_member_ids: set[str] = set()
    for conn in design.connections:
        connection_member_ids.add(conn.a)
        connection_member_ids.add(conn.b)
        connected_member_ids.add(conn.a)
        connected_member_ids.add(conn.b)

    return ValidationContext(
        design=design,
        constraints=constraints,
        analysis=analysis,
        material_props=material_props,
        member_by_id=member_by_id,
        connection_member_ids=connection_member_ids,
        connected_member_ids=connected_member_ids,
        rule_set_version=rule_set_version,
    )
