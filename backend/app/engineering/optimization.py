"""
Design Optimization Engine — Multi-Objective Pareto Analysis

Evaluates multiple design candidates across weighted criteria and
identifies Pareto-optimal solutions. No LLM calls — pure scoring.

Objectives:
  1. Minimize cost (USD)
  2. Maximize structural integrity (score 0-100)
  3. Maximize compliance (score 0-100)
  4. Minimize build complexity (score 0-100, lower = simpler)
  5. Maximize material availability (score 0-100)

References:
  - Zitzler & Thiele (1998) Strength Pareto Evolutionary Algorithm
  - SkyCiv design comparison methodology
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


# -------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------

@dataclass
class DesignCandidate:
    """A single design candidate with scored attributes."""
    design_id: str
    name: str
    cost_usd: float
    structural_score: float  # 0-100
    compliance_score: float  # 0-100
    build_complexity: float  # 0-100 (lower = simpler)
    material_availability: float  # 0-100
    member_count: int = 0
    span_m: float = 0.0
    height_m: float = 0.0
    total_weight_kg: float = 0.0
    materials_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_id": self.design_id,
            "name": self.name,
            "cost_usd": round(self.cost_usd, 2),
            "structural_score": round(self.structural_score, 1),
            "compliance_score": round(self.compliance_score, 1),
            "build_complexity": round(self.build_complexity, 1),
            "material_availability": round(self.material_availability, 1),
            "member_count": self.member_count,
            "span_m": self.span_m,
            "height_m": self.height_m,
            "total_weight_kg": round(self.total_weight_kg, 1),
        }


@dataclass
class OptimizationCriteria:
    """Weighted criteria for multi-objective optimization."""
    cost_weight: float = 0.25
    structural_weight: float = 0.30
    compliance_weight: float = 0.20
    build_complexity_weight: float = 0.15
    material_availability_weight: float = 0.10

    def normalize(self):
        total = (self.cost_weight + self.structural_weight +
                 self.compliance_weight + self.build_complexity_weight +
                 self.material_availability_weight)
        if total > 0:
            self.cost_weight /= total
            self.structural_weight /= total
            self.compliance_weight /= total
            self.build_complexity_weight /= total
            self.material_availability_weight /= total


@dataclass
class ScoredDesign:
    """Design with computed scores and Pareto information."""
    design: DesignCandidate
    normalized_scores: dict[str, float]
    weighted_score: float
    is_pareto_optimal: bool
    pareto_rank: int  # 0 = non-dominated, 1 = dominated by rank-0, etc.
    dominance_count: int  # how many designs dominate this one
    dominates_count: int  # how many designs this dominates
    rank_label: str  # "Best Value", "Pareto Optimal", etc.

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.design.to_dict(),
            "normalized_scores": {k: round(v, 4) for k, v in self.normalized_scores.items()},
            "weighted_score": round(self.weighted_score, 4),
            "is_pareto_optimal": self.is_pareto_optimal,
            "pareto_rank": self.pareto_rank,
            "dominance_count": self.dominance_count,
            "dominates_count": self.dominates_count,
            "rank_label": self.rank_label,
        }


@dataclass
class OptimizationResult:
    """Complete optimization result."""
    candidates: list[ScoredDesign]
    pareto_front: list[ScoredDesign]
    best_value: ScoredDesign | None
    best_structural: ScoredDesign | None
    best_cost: ScoredDesign | None
    criteria: OptimizationCriteria
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates": [c.to_dict() for c in self.candidates],
            "pareto_front": [c.to_dict() for c in self.pareto_front],
            "recommendations": {
                "best_value": self.best_value.to_dict() if self.best_value else None,
                "best_structural": self.best_structural.to_dict() if self.best_structural else None,
                "best_cost": self.best_cost.to_dict() if self.best_cost else None,
            },
            "criteria": {
                "cost_weight": round(self.criteria.cost_weight, 3),
                "structural_weight": round(self.criteria.structural_weight, 3),
                "compliance_weight": round(self.criteria.compliance_weight, 3),
                "build_complexity_weight": round(self.criteria.build_complexity_weight, 3),
                "material_availability_weight": round(self.criteria.material_availability_weight, 3),
            },
            "summary": self.summary,
        }


# -------------------------------------------------------------------
# Pareto front computation
# -------------------------------------------------------------------

def _dominates(a: DesignCandidate, b: DesignCandidate) -> bool:
    """Check if design A dominates design B (maximization for all except cost and complexity)."""
    # For cost and complexity: lower is better
    # For structural, compliance, availability: higher is better
    better_in_any = False

    # Cost: a is better if <= b
    if a.cost_usd < b.cost_usd:
        better_in_any = True
    elif a.cost_usd > b.cost_usd:
        return False

    # Structural: a is better if >= b
    if a.structural_score > b.structural_score:
        better_in_any = True
    elif a.structural_score < b.structural_score:
        return False

    # Compliance: a is better if >= b
    if a.compliance_score > b.compliance_score:
        better_in_any = True
    elif a.compliance_score < b.compliance_score:
        return False

    # Build complexity: a is better if <= b
    if a.build_complexity < b.build_complexity:
        better_in_any = True
    elif a.build_complexity > b.build_complexity:
        return False

    # Material availability: a is better if >= b
    if a.material_availability > b.material_availability:
        better_in_any = True
    elif a.material_availability < b.material_availability:
        return False

    return better_in_any


def _compute_pareto_fronts(candidates: list[DesignCandidate]) -> list[int]:
    """
    Compute Pareto ranks using iterative non-dominated sorting.
    Returns a list of ranks (0 = first front, 1 = second front, etc.)
    """
    n = len(candidates)
    ranks = [0] * n
    remaining = list(range(n))

    current_rank = 0
    while remaining:
        front = []
        dominated_set = set()

        for i in remaining:
            is_dominated = False
            for j in remaining:
                if i != j and _dominates(candidates[j], candidates[i]):
                    is_dominated = True
                    break
            if not is_dominated:
                front.append(i)

        for idx in front:
            ranks[idx] = current_rank
        remaining = [i for i in remaining if i not in front]
        current_rank += 1

    return ranks


def _normalize(value: float, min_val: float, max_val: float, invert: bool = False) -> float:
    """Min-max normalize to [0, 1]. If invert, 1 is best."""
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    if invert:
        normalized = 1.0 - normalized
    return max(0.0, min(1.0, normalized))


# -------------------------------------------------------------------
# Main optimization function
# -------------------------------------------------------------------

def optimize_designs(
    candidates: list[DesignCandidate],
    criteria: OptimizationCriteria | None = None,
) -> OptimizationResult:
    """
    Run multi-objective optimization on a set of design candidates.

    Args:
        candidates: List of designs to evaluate.
        criteria: Weighted criteria (default: equal weights).

    Returns:
        OptimizationResult with scored designs, Pareto front, and recommendations.
    """
    if not candidates:
        return OptimizationResult(
            candidates=[], pareto_front=[], best_value=None,
            best_structural=None, best_cost=None,
            criteria=criteria or OptimizationCriteria(),
            summary={"total_candidates": 0},
        )

    if criteria is None:
        criteria = OptimizationCriteria()
    criteria.normalize()

    # Compute Pareto ranks
    ranks = _compute_pareto_fronts(candidates)

    # Compute min/max for normalization
    costs = [c.cost_usd for c in candidates]
    structural = [c.structural_score for c in candidates]
    compliance = [c.compliance_score for c in candidates]
    complexity = [c.build_complexity for c in candidates]
    availability = [c.material_availability for c in candidates]

    # Score each candidate
    scored: list[ScoredDesign] = []
    for i, cand in enumerate(candidates):
        norm = {
            "cost": _normalize(cand.cost_usd, min(costs), max(costs), invert=True),
            "structural": _normalize(cand.structural_score, min(structural), max(structural)),
            "compliance": _normalize(cand.compliance_score, min(compliance), max(compliance)),
            "build_complexity": _normalize(cand.build_complexity, min(complexity), max(complexity), invert=True),
            "material_availability": _normalize(cand.material_availability, min(availability), max(availability)),
        }

        weighted = (
            norm["cost"] * criteria.cost_weight +
            norm["structural"] * criteria.structural_weight +
            norm["compliance"] * criteria.compliance_weight +
            norm["build_complexity"] * criteria.build_complexity_weight +
            norm["material_availability"] * criteria.material_availability_weight
        )

        # Count dominance
        dominates_count = sum(1 for j, other in enumerate(candidates) if j != i and _dominates(cand, other))
        dominance_count = sum(1 for j, other in enumerate(candidates) if j != i and _dominates(other, cand))

        is_pareto = ranks[i] == 0

        if is_pareto and weighted == max(s.weighted_score for s in scored or [ScoredDesign(design=cand, normalized_scores=norm, weighted_score=weighted, is_pareto_optimal=True, pareto_rank=0, dominance_count=dominance_count, dominates_count=dominates_count, rank_label="Best Value")]):
            rank_label = "Best Value (Pareto Optimal)"
        elif is_pareto:
            rank_label = "Pareto Optimal"
        elif ranks[i] == 1:
            rank_label = "Near-Optimal"
        else:
            rank_label = "Sub-Optimal"

        scored.append(ScoredDesign(
            design=cand,
            normalized_scores=norm,
            weighted_score=weighted,
            is_pareto_optimal=is_pareto,
            pareto_rank=ranks[i],
            dominance_count=dominance_count,
            dominates_count=dominates_count,
            rank_label=rank_label,
        ))

    # Sort by weighted score descending
    scored.sort(key=lambda s: s.weighted_score, reverse=True)

    # Fix "Best Value" label
    if scored:
        scored[0].rank_label = "Best Value (Pareto Optimal)" if scored[0].is_pareto_optimal else "Best Value"

    # Find recommendations
    best_value = scored[0] if scored else None
    best_structural = max(scored, key=lambda s: s.design.structural_score) if scored else None
    best_cost = min(scored, key=lambda s: s.design.cost_usd) if scored else None

    pareto_front = [s for s in scored if s.is_pareto_optimal]

    summary = {
        "total_candidates": len(candidates),
        "pareto_optimal_count": len(pareto_front),
        "best_weighted_score": round(best_value.weighted_score, 4) if best_value else 0,
        "score_range": {
            "min": round(min(s.weighted_score for s in scored), 4) if scored else 0,
            "max": round(max(s.weighted_score for s in scored), 4) if scored else 0,
        },
    }

    return OptimizationResult(
        candidates=scored,
        pareto_front=pareto_front,
        best_value=best_value,
        best_structural=best_structural,
        best_cost=best_cost,
        criteria=criteria,
        summary=summary,
    )
