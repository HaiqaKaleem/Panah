"""Advanced analytics service — prediction models, trend analysis, and insights."""

import math
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from fastapi import APIRouter, Query

router = APIRouter(prefix="/analytics", tags=["Advanced Analytics"])


@dataclass
class TrendPoint:
    date: str
    value: float
    label: str = ""


class AnalyticsEngine:
    """Advanced analytics with trend analysis and predictions."""

    def __init__(self):
        self._events: list[dict] = []

    def record_event(self, event_type: str, entity_type: str, entity_id: str,
                     metadata: Optional[dict] = None):
        """Record an analytics event."""
        self._events.append({
            "type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        })

    def get_usage_trends(self, days: int = 30) -> dict:
        """Analyze usage trends over time."""
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)

        # Filter events
        recent = [e for e in self._events if datetime.fromisoformat(e["timestamp"]) > cutoff]

        # Group by day
        daily_counts = {}
        for event in recent:
            day = event["timestamp"][:10]
            daily_counts[day] = daily_counts.get(day, 0) + 1

        # Calculate trend (simple linear regression)
        if len(daily_counts) >= 2:
            values = list(daily_counts.values())
            avg = sum(values) / len(values)
            trend = "increasing" if values[-1] > avg else "decreasing" if values[-1] < avg else "stable"
        else:
            avg = 0
            trend = "insufficient_data"

        return {
            "period_days": days,
            "total_events": len(recent),
            "daily_average": round(avg, 1),
            "trend": trend,
            "daily_counts": daily_counts,
        }

    def get_entity_popularity(self) -> dict:
        """Analyze which entity types are most used."""
        counts = {}
        for event in self._events:
            et = event["entity_type"]
            counts[et] = counts.get(et, 0) + 1

        # Sort by popularity
        sorted_entities = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_events": len(self._events),
            "entities": [
                {"type": et, "count": count, "percentage": round(count / max(len(self._events), 1) * 100, 1)}
                for et, count in sorted_entities
            ],
        }

    def predict_design_success(self, design_data: dict) -> dict:
        """Predict design approval probability based on historical data."""
        # Simple scoring model (in production, use ML)
        score = 50  # Base score

        # Factor 1: Material quality
        if design_data.get("material_quality_score", 0) > 70:
            score += 15

        # Factor 2: Structural safety
        if design_data.get("safety_factor", 0) > 1.5:
            score += 20
        elif design_data.get("safety_factor", 0) > 1.2:
            score += 10

        # Factor 3: Compliance
        if design_data.get("compliance_score", 0) > 80:
            score += 15
        elif design_data.get("compliance_score", 0) > 60:
            score += 5

        # Factor 4: Cost efficiency
        if design_data.get("cost_per_person", 0) < 100:
            score += 10

        # Factor 5: Build complexity (lower is better)
        complexity = design_data.get("build_complexity", 5)
        if complexity < 3:
            score += 10
        elif complexity < 5:
            score += 5

        # Clamp
        score = min(100, max(0, score))

        # Determine risk level
        if score >= 80:
            risk = "low"
            recommendation = "High likelihood of approval. Proceed with submission."
        elif score >= 60:
            risk = "medium"
            recommendation = "Moderate likelihood. Consider addressing weak areas before submission."
        else:
            risk = "high"
            recommendation = "Significant improvements needed. Review structural and compliance factors."

        return {
            "approval_probability": score,
            "risk_level": risk,
            "recommendation": recommendation,
            "factors": {
                "material_quality": design_data.get("material_quality_score", 0),
                "safety_factor": design_data.get("safety_factor", 1.0),
                "compliance": design_data.get("compliance_score", 0),
                "cost_efficiency": design_data.get("cost_per_person", 0),
                "complexity": design_data.get("build_complexity", 5),
            },
        }

    def get_performance_metrics(self) -> dict:
        """Get system performance metrics."""
        total = len(self._events)
        if total == 0:
            return {"status": "no_data"}

        # Event type distribution
        type_counts = {}
        for e in self._events:
            t = e["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        # Hourly distribution
        hourly = {}
        for e in self._events:
            hour = e["timestamp"][11:13]
            hourly[hour] = hourly.get(hour, 0) + 1

        # Peak hour
        peak_hour = max(hourly.items(), key=lambda x: x[1])[0] if hourly else "N/A"

        return {
            "total_events": total,
            "event_types": type_counts,
            "peak_hour": f"{peak_hour}:00",
            "hourly_distribution": hourly,
            "avg_events_per_day": round(total / max(1, len(set(e["timestamp"][:10] for e in self._events))), 1),
        }

    def get_cost_analytics(self, designs: list[dict]) -> dict:
        """Analyze cost trends across designs."""
        if not designs:
            return {"status": "no_data"}

        costs = [d.get("total_cost", 0) for d in designs]
        per_person = [d.get("cost_per_person", 0) for d in designs if d.get("cost_per_person")]

        return {
            "total_designs": len(designs),
            "avg_cost": round(sum(costs) / len(costs), 2) if costs else 0,
            "min_cost": min(costs) if costs else 0,
            "max_cost": max(costs) if costs else 0,
            "avg_cost_per_person": round(sum(per_person) / len(per_person), 2) if per_person else 0,
            "cost_range": {
                "min": min(costs) if costs else 0,
                "max": max(costs) if costs else 0,
            },
        }


analytics_engine = AnalyticsEngine()


# ── API Endpoints ─────────────────────────────────────────────────────

@router.get("/trends", summary="Usage trends and analytics")
async def usage_trends(days: int = Query(30, ge=1, le=365)):
    """Analyze usage trends over time with daily counts and trend direction."""
    return analytics_engine.get_usage_trends(days)


@router.get("/entity-popularity", summary="Entity usage popularity")
async def entity_popularity():
    """Which entity types are most used across the platform."""
    return analytics_engine.get_entity_popularity()


@router.post("/predict", summary="Predict design approval probability")
async def predict_design(data: dict):
    """
    Predict the probability of a design being approved by an engineer.

    Input design metrics:
    - **material_quality_score**: 0-100
    - **safety_factor**: 1.0-3.0
    - **compliance_score**: 0-100
    - **cost_per_person**: USD per person
    - **build_complexity**: 1-10
    """
    return analytics_engine.predict_design_success(data)


@router.get("/performance", summary="System performance metrics")
async def performance_metrics():
    """Get system performance metrics including peak hours and event distribution."""
    return analytics_engine.get_performance_metrics()


@router.post("/cost-analysis", summary="Cost analytics across designs")
async def cost_analysis(designs: list[dict]):
    """Analyze cost trends and statistics across multiple designs."""
    return analytics_engine.get_cost_analytics(designs)


@router.post("/record", summary="Record an analytics event")
async def record_event(event: dict):
    """Record a custom analytics event."""
    analytics_engine.record_event(
        event_type=event.get("type", "custom"),
        entity_type=event.get("entity_type", "unknown"),
        entity_id=event.get("entity_id", ""),
        metadata=event.get("metadata", {}),
    )
    return {"status": "recorded"}
