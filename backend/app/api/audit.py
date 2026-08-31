from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.audit import get_audit_events

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None
    actor_id: str
    action: str
    object_type: str
    object_id: str
    details_json: str | None
    created_at: object


@router.get("", response_model=list[AuditEventResponse])
def list_audit_events(
    project_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return get_audit_events(db, project_id=project_id, limit=limit)
