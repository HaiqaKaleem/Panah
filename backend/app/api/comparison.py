"""Design Comparison API — weighted scoring matrix for comparing generated designs."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.generated_design import GeneratedDesign

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}",
    tags=["Design Comparison"],
)


class ScoringCriterion(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    weight: float = Field(default=1.0, gt=0, le=10)
    max_score: float = Field(default=10.0, gt=0, le=10)


class CompareRequest(BaseModel):
    design_ids: list[int] = Field(..., min_length=2, max_length=10)
    criteria: list[ScoringCriterion] = Field(
        default_factory=lambda: [
            ScoringCriterion(name="Structural Integrity", weight=3.0, max_score=10.0),
            ScoringCriterion(name="Compliance Score", weight=2.5, max_score=10.0),
            ScoringCriterion(name="Cost Efficiency", weight=2.0, max_score=10.0),
            ScoringCriterion(name="Material Availability", weight=1.5, max_score=10.0),
            ScoringCriterion(name="Build Complexity", weight=1.0, max_score=10.0),
        ]
    )


def _compute_score(analysis: dict, rules: dict) -> dict[str, float]:
    """Extract normalized scores from analysis and rules for one design."""
    # Structural Integrity: map integrity_score (0-100) to 0-10
    integrity = analysis.get("overall_integrity_score") or 0.0
    structural_score = min(10.0, integrity / 10.0)

    # Compliance Score: map rules score (0-100) to 0-10
    compliance_pct = rules.get("score", 0.0)
    compliance_score = min(10.0, compliance_pct / 10.0)

    # Cost Efficiency: based on dead load (lighter = cheaper)
    dead_load = analysis.get("dead_load_kg", 100.0)
    cost_score = max(0.0, min(10.0, 10.0 - (dead_load / 50.0)))

    # Material Availability: count local materials (higher = more local)
    # Default neutral score
    availability_score = 6.0

    # Build Complexity: fewer members = simpler = better
    # (can't count from here, default neutral)
    complexity_score = 5.0

    return {
        "Structural Integrity": round(structural_score, 2),
        "Compliance Score": round(compliance_score, 2),
        "Cost Efficiency": round(cost_score, 2),
        "Material Availability": round(availability_score, 2),
        "Build Complexity": round(complexity_score, 2),
    }


@router.post("/compare-designs")
def compare_designs(payload: CompareRequest, project_id: int, site_id: int, db: Session = Depends(get_db)):
    """
    Compare multiple generated designs using a weighted scoring matrix.
    Returns ranked designs with per-criterion scores and total weighted score.
    """
    import json

    designs = []
    for did in payload.design_ids:
        record = db.get(GeneratedDesign, did)
        if record is None or record.site_id != site_id:
            raise HTTPException(status_code=404, detail=f"Design {did} not found")
        designs.append(record)

    # Normalize criterion weights
    total_weight = sum(c.weight for c in payload.criteria)

    results = []
    for design in designs:
        analysis = json.loads(design.analysis_json)
        rules = json.loads(design.rules_json)

        raw_scores = _compute_score(analysis, rules)

        weighted_total = 0.0
        criterion_scores = []
        for criterion in payload.criteria:
            raw = raw_scores.get(criterion.name, 5.0)
            normalized = raw / criterion.max_score  # 0-1
            weighted = normalized * (criterion.weight / total_weight) * 100
            weighted_total += weighted
            criterion_scores.append({
                "criterion": criterion.name,
                "raw_score": raw,
                "max_score": criterion.max_score,
                "weight": criterion.weight,
                "weighted_score": round(weighted, 2),
            })

        results.append({
            "design_id": design.id,
            "candidate_id": design.candidate_id,
            "version": design.version,
            "status": design.status,
            "total_weighted_score": round(weighted_total, 2),
            "criteria": criterion_scores,
            "integrity_score": analysis.get("overall_integrity_score"),
            "compliant": rules.get("compliant", False),
            "blocking_rules": rules.get("summary", {}).get("blocking", 0),
        })

    # Sort by total weighted score descending
    results.sort(key=lambda r: r["total_weighted_score"], reverse=True)

    # Add rank
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {
        "criteria": [c.model_dump() for c in payload.criteria],
        "total_weight": total_weight,
        "results": results,
        "winner": results[0] if results else None,
    }
