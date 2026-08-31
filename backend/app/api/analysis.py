import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.ai.factory import get_vision_provider
from app.core.database import get_db
from app.models.observation import Observation
from app.api.observations import get_media_or_404
from app.storage.factory import get_media_storage

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/captures/{capture_id}/media/{media_id}",
    tags=["AI Analysis"]
)

@router.post("/analyze", status_code=201)
def analyze_media(project_id: int, site_id: int, capture_id: int, media_id: int, db: Session = Depends(get_db)):
    media = get_media_or_404(project_id, site_id, capture_id, media_id, db)
    try:
        path = get_media_storage().get_path(media.storage_key)
    except FileNotFoundError:
        raise HTTPException(404, "Media file not found")

    try:
        candidates = get_vision_provider().analyze_media(str(path), media.mime_type)
    except Exception as exc:
        raise HTTPException(502, f"AI provider failed: {exc}")

    created = []
    for candidate in candidates:
        if not 0 <= candidate.confidence <= 1:
            raise HTTPException(502, "AI provider returned invalid confidence")
        item = Observation(
            media_id=media.id,
            observation_type=candidate.observation_type,
            label=candidate.label.strip(),
            confidence=candidate.confidence,
            status="unconfirmed",
            bbox_x=candidate.bbox_x,
            bbox_y=candidate.bbox_y,
            bbox_width=candidate.bbox_width,
            bbox_height=candidate.bbox_height,
            evidence_timestamp_seconds=candidate.evidence_timestamp_seconds,
            analysis_metadata_json=json.dumps(candidate.analysis_metadata or {}),
        )
        db.add(item)
        created.append(item)

    db.commit()
    for item in created:
        db.refresh(item)

    return {
        "media_id": media.id,
        "status": "complete",
        "observations_created": len(created),
        "observations": [
            {"id": x.id, "observation_type": x.observation_type,
             "label": x.label, "confidence": x.confidence, "status": x.status}
            for x in created
        ]
    }
