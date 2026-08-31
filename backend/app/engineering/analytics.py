"""
Analytics Engine — Platform usage statistics and insights.

Provides aggregated metrics, trends, and insights from the audit trail
and validation history. Useful for dashboards and monitoring.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent
from app.models.project import Project
from app.models.generated_design import GeneratedDesign
from app.models.validation import ValidationRun, ValidationResult
from app.models.review import Review


def get_platform_analytics(db: Session) -> dict[str, Any]:
    """Get comprehensive platform analytics."""
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    total_designs = db.query(func.count(GeneratedDesign.id)).scalar() or 0
    total_validations = db.query(func.count(ValidationRun.id)).scalar() or 0
    total_reviews = db.query(func.count(Review.id)).scalar() or 0
    total_audit_events = db.query(func.count(AuditEvent.id)).scalar() or 0

    # Validation pass/fail rates
    validation_results = db.query(ValidationResult.status).all()
    status_counts = Counter(r[0] for r in validation_results) if validation_results else Counter()
    total_val_results = sum(status_counts.values()) or 1

    # Review outcomes
    review_decisions = db.query(Review.decision).all() if hasattr(Review, "decision") else []
    decision_counts = Counter(r[0] for r in review_decisions) if review_decisions else Counter()

    # Action distribution from audit trail
    actions = db.query(AuditEvent.action).all()
    action_counts = Counter(a[0] for a in actions) if actions else Counter()

    # Recent activity (last 7 days)
    recent_cutoff = datetime.now(timezone.utc)
    from datetime import timedelta
    recent_cutoff = recent_cutoff - timedelta(days=7)
    recent_events = db.query(func.count(AuditEvent.id)).filter(
        AuditEvent.timestamp >= recent_cutoff
    ).scalar() or 0

    return {
        "overview": {
            "total_projects": total_projects,
            "total_designs_generated": total_designs,
            "total_validations": total_validations,
            "total_reviews": total_reviews,
            "total_audit_events": total_audit_events,
            "recent_activity_7d": recent_events,
        },
        "validation_metrics": {
            "total_results": total_val_results,
            "pass_rate": round(status_counts.get("pass", 0) / total_val_results * 100, 1),
            "fail_rate": round(status_counts.get("fail", 0) / total_val_results * 100, 1),
            "review_rate": round(status_counts.get("review", 0) / total_val_results * 100, 1),
            "status_breakdown": dict(status_counts),
        },
        "review_metrics": {
            "total_decisions": sum(decision_counts.values()),
            "approval_rate": round(
                decision_counts.get("approved", 0) / max(sum(decision_counts.values()), 1) * 100, 1
            ),
            "decision_breakdown": dict(decision_counts),
        },
        "action_distribution": dict(action_counts.most_common(20)),
        "insights": _generate_insights(total_projects, total_designs, status_counts, decision_counts),
    }


def _generate_insights(
    projects: int,
    designs: int,
    validation_status: Counter,
    review_decisions: Counter,
) -> list[str]:
    """Generate actionable insights from the data."""
    insights = []

    if projects == 0:
        insights.append("No projects created yet. Start by creating a project with site data.")
    elif designs == 0:
        insights.append(f"{projects} project(s) created but no designs generated yet. Run the constraint-based generator.")
    else:
        total_v = sum(validation_status.values())
        if total_v > 0:
            pass_rate = validation_status.get("pass", 0) / total_v
            if pass_rate < 0.5:
                insights.append("Less than 50% of validations pass. Consider relaxing constraints or improving material selection.")
            elif pass_rate > 0.8:
                insights.append(f"Strong validation pass rate ({pass_rate:.0%}). Designs are meeting Sphere Handbook standards.")

        total_r = sum(review_decisions.values())
        if total_r > 0:
            approval_rate = review_decisions.get("approved", 0) / total_r
            if approval_rate < 0.6:
                insights.append("Low approval rate in engineer reviews. Designs may need more structural refinement.")

    if projects > 0 and designs / max(projects, 1) < 1:
        insights.append("Average designs per project is low. Consider generating more candidates for better optimization.")

    if not insights:
        insights.append("Platform is operational. Create a project and generate designs to see insights.")

    return insights
