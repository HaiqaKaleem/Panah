"""
Material Substitution Recommender

Suggests alternative materials when the primary choice is unavailable,
based on structural property similarity, cost, and local availability.

Uses a compatibility scoring algorithm:
  - Elastic modulus ratio (closer to 1.0 = better)
  - Density ratio
  - Cost ratio
  - Availability bonus
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.materials.catalog import MATERIAL_CATALOG, MaterialProperties


@dataclass
class SubstitutionRecommendation:
    """A recommended material substitution."""
    original_type: str
    recommended_type: str
    display_name: str
    compatibility_score: float  # 0-100
    elastic_modulus_ratio: float
    density_ratio: float
    cost_ratio: float
    availability: str
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_type": self.original_type,
            "recommended_type": self.recommended_type,
            "display_name": self.display_name,
            "compatibility_score": round(self.compatibility_score, 1),
            "elastic_modulus_ratio": round(self.elastic_modulus_ratio, 2),
            "density_ratio": round(self.density_ratio, 2),
            "cost_ratio": round(self.cost_ratio, 2),
            "availability": self.availability,
            "notes": self.notes,
        }


def _compatibility_score(original: MaterialProperties, candidate: MaterialProperties) -> tuple[float, list[str]]:
    """
    Score how compatible a candidate material is as a substitute.
    Returns (score 0-100, list of notes).
    """
    notes: list[str] = []

    # Elastic modulus ratio (most important for structural behavior)
    em_ratio = candidate.elastic_modulus_pa / original.elastic_modulus_pa if original.elastic_modulus_pa > 0 else 1.0
    em_score = max(0, 100 - abs(em_ratio - 1.0) * 100)
    if em_ratio < 0.5:
        notes.append(f"Significantly less stiff ({em_ratio:.0%} of original)")
    elif em_ratio > 1.5:
        notes.append(f"Significantly stiffer ({em_ratio:.0%} of original)")
    elif 0.8 <= em_ratio <= 1.2:
        notes.append("Similar stiffness to original")

    # Density ratio
    density_ratio = candidate.density_kg_m3 / original.density_kg_m3 if original.density_kg_m3 > 0 else 1.0
    density_score = max(0, 100 - abs(density_ratio - 1.0) * 50)

    # Allowable stress ratio
    stress_ratio = candidate.allowable_axial_stress_pa / original.allowable_axial_stress_pa if original.allowable_axial_stress_pa > 0 else 1.0
    stress_score = max(0, 100 - abs(stress_ratio - 1.0) * 80)
    if stress_ratio < 0.7:
        notes.append("Lower allowable stress — may need larger cross-section")

    # Cost ratio (lower is better)
    cost_ratio = candidate.unit_cost_usd / original.unit_cost_usd if original.unit_cost_usd > 0 else 1.0
    cost_score = 100 if cost_ratio <= 1.0 else max(0, 100 - (cost_ratio - 1.0) * 50)
    if cost_ratio < 0.8:
        notes.append("More cost-effective than original")
    elif cost_ratio > 1.5:
        notes.append("Significantly more expensive")

    # Availability bonus
    avail_bonus = 0
    if candidate.local_availability == "available":
        avail_bonus = 15
        notes.append("Readily available locally")
    elif candidate.local_availability == "limited":
        avail_bonus = 5
    elif candidate.local_availability == "imported":
        avail_bonus = 0
        notes.append("Imported — may have supply chain delays")

    # Lifespan comparison
    if candidate.expected_lifespan_years < original.expected_lifespan_years * 0.5:
        notes.append(f"Shorter lifespan ({candidate.expected_lifespan_years:.0f}y vs {original.expected_lifespan_years:.0f}y)")

    # Weighted score
    score = (
        em_score * 0.35 +
        stress_score * 0.25 +
        density_score * 0.10 +
        cost_score * 0.15 +
        avail_bonus
    )

    return min(100.0, max(0.0, score)), notes


def recommend_substitutions(
    material_type: str,
    max_recommendations: int = 3,
) -> list[SubstitutionRecommendation]:
    """
    Recommend material substitutes for a given material type.

    Args:
        material_type: The material type to find substitutes for.
        max_recommendations: Maximum number of recommendations.

    Returns:
        List of SubstitutionRecommendation, sorted by compatibility score.
    """
    original = MATERIAL_CATALOG.get(material_type)
    if original is None:
        return []

    recommendations: list[SubstitutionRecommendation] = []

    for candidate_type, candidate in MATERIAL_CATALOG.items():
        if candidate_type == material_type:
            continue

        score, notes = _compatibility_score(original, candidate)

        recommendations.append(SubstitutionRecommendation(
            original_type=material_type,
            recommended_type=candidate_type,
            display_name=candidate.display_name,
            compatibility_score=score,
            elastic_modulus_ratio=candidate.elastic_modulus_pa / original.elastic_modulus_pa if original.elastic_modulus_pa > 0 else 1.0,
            density_ratio=candidate.density_kg_m3 / original.density_kg_m3 if original.density_kg_m3 > 0 else 1.0,
            cost_ratio=candidate.unit_cost_usd / original.unit_cost_usd if original.unit_cost_usd > 0 else 1.0,
            availability=candidate.local_availability,
            notes=notes,
        ))

    # Sort by compatibility score descending
    recommendations.sort(key=lambda r: r.compatibility_score, reverse=True)

    return recommendations[:max_recommendations]
