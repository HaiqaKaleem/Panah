import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.capture import Capture
from app.models.media import Media
from app.models.observation import Observation
from app.models.site import Site
from app.schemas.observation import ObservationCreate, ObservationResponse, ObservationStatusUpdate

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/captures/{capture_id}/media/{media_id}/observations",
    tags=["Observations"]
)

def get_media_or_404(project_id, site_id, capture_id, media_id, db):
    site = db.get(Site, site_id)
    if site is None or site.project_id != project_id:
        raise HTTPException(404, "Site not found")
    capture = db.get(Capture, capture_id)
    if capture is None or capture.site_id != site_id:
        raise HTTPException(404, "Capture not found")
    media = db.get(Media, media_id)
    if media is None or media.capture_id != capture_id:
        raise HTTPException(404, "Media not found")
    return media

def validate_bbox(payload):
    vals = [payload.bbox_x, payload.bbox_y, payload.bbox_width, payload.bbox_height]
    if any(v is not None for v in vals):
        if any(v is None for v in vals):
            raise HTTPException(422, "Bounding box requires x, y, width, and height")
        if payload.bbox_x + payload.bbox_width > 1:
            raise HTTPException(422, "Bounding box exceeds media width")
        if payload.bbox_y + payload.bbox_height > 1:
            raise HTTPException(422, "Bounding box exceeds media height")

@router.post("", response_model=ObservationResponse, status_code=201)
def create_observation(project_id: int, site_id: int, capture_id: int, media_id: int, payload: ObservationCreate, db: Session = Depends(get_db)):
    get_media_or_404(project_id, site_id, capture_id, media_id, db)
    validate_bbox(payload)
    item = Observation(
        media_id=media_id,
        observation_type=payload.observation_type,
        label=payload.label,
        confidence=payload.confidence,
        status="unconfirmed",
        bbox_x=payload.bbox_x, bbox_y=payload.bbox_y,
        bbox_width=payload.bbox_width, bbox_height=payload.bbox_height,
        evidence_timestamp_seconds=payload.evidence_timestamp_seconds,
        analysis_metadata_json=json.dumps(payload.analysis_metadata) if payload.analysis_metadata is not None else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("", response_model=list[ObservationResponse])
def list_observations(project_id: int, site_id: int, capture_id: int, media_id: int, db: Session = Depends(get_db)):
    get_media_or_404(project_id, site_id, capture_id, media_id, db)
    stmt = select(Observation).where(Observation.media_id == media_id).order_by(Observation.created_at.desc())
    return list(db.scalars(stmt).all())

@router.patch("/{observation_id}/status", response_model=ObservationResponse)
def update_status(project_id: int, site_id: int, capture_id: int, media_id: int, observation_id: int, payload: ObservationStatusUpdate, db: Session = Depends(get_db)):
    get_media_or_404(project_id, site_id, capture_id, media_id, db)
    item = db.get(Observation, observation_id)
    if item is None or item.media_id != media_id:
        raise HTTPException(404, "Observation not found")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return item
