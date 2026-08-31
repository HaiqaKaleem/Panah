import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def log_event(
    db: Session,
    *,
    project_id: int | None = None,
    actor_id: str = "system",
    action: str,
    object_type: str,
    object_id: str,
    details: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        project_id=project_id,
        actor_id=actor_id,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        details_json=json.dumps(details) if details else None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    return event


def get_audit_events(
    db: Session,
    project_id: int | None = None,
    limit: int = 50,
) -> list[AuditEvent]:
    query = db.query(AuditEvent)
    if project_id is not None:
        query = query.filter(AuditEvent.project_id == project_id)
    return query.order_by(AuditEvent.id.desc()).limit(limit).all()
