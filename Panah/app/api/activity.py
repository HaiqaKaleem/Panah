"""Activity Timeline API — chronological activity feed per project."""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import AuditEvent
from app.services.audit import get_audit_events

router = APIRouter(prefix="/projects/{project_id}/activity", tags=["Activity"])


@router.get("")
def get_activity_timeline(
    project_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    action_filter: str | None = Query(default=None, description="Filter by action type"),
    db: Session = Depends(get_db),
):
    """
    Return a chronological activity feed for a project.
    Supports pagination, filtering by action type.
    """
    query = db.query(AuditEvent).filter(AuditEvent.project_id == project_id)

    if action_filter:
        query = query.filter(AuditEvent.action == action_filter)

    total = query.count()

    events = (
        query.order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Human-readable action labels
    ACTION_LABELS = {
        "design_candidate_generated": "Design candidates generated",
        "validation_run": "Validation completed",
        "review_submitted": "Review submitted",
        "review_decision": "Review decision recorded",
        "generated_design_validated": "Design validated",
        "generated_design_promoted": "Design promoted to version",
    }

    items = []
    for event in events:
        items.append({
            "id": event.id,
            "action": event.action,
            "action_label": ACTION_LABELS.get(event.action, event.action),
            "object_type": event.object_type,
            "object_id": event.object_id,
            "actor_id": event.actor_id,
            "details": json.loads(event.details_json) if event.details_json else {},
            "created_at": event.created_at.isoformat() if event.created_at else None,
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
        "items": items,
    }


@router.get("/summary")
def get_activity_summary(project_id: int, db: Session = Depends(get_db)):
    """Return a summary of activity by type for the dashboard."""
    from sqlalchemy import func

    results = (
        db.query(AuditEvent.action, func.count(AuditEvent.id))
        .filter(AuditEvent.project_id == project_id)
        .group_by(AuditEvent.action)
        .all()
    )

    return {
        "project_id": project_id,
        "by_action": {action: count for action, count in results},
        "total_events": sum(count for _, count in results),
    }

