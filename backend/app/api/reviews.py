from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.design_version import DesignVersion
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewDecisionUpdate, ReviewResponse
from app.services.audit import log_event

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/design-versions",
    tags=["Reviews"],
)


def get_design_version_or_404(project_id: int, site_id: int, version_id: int, db: Session) -> DesignVersion:
    dv = db.get(DesignVersion, version_id)
    if dv is None or dv.site_id != site_id:
        raise HTTPException(status_code=404, detail="Design version not found")
    return dv


@router.post("/{version_id}/submit-review", response_model=ReviewResponse, status_code=201)
def submit_review(project_id: int, site_id: int, version_id: int, payload: ReviewCreate, db: Session = Depends(get_db)):
    get_design_version_or_404(project_id, site_id, version_id, db)

    review = Review(
        design_version_id=version_id,
        reviewer_id=payload.reviewer_id,
        decision="pending",
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    log_event(
        db,
        project_id=project_id,
        action="review_submitted",
        object_type="review",
        object_id=str(review.id),
        details={"design_version_id": version_id, "reviewer": payload.reviewer_id},
    )
    db.commit()

    return review


@router.post("/reviews/{review_id}/decision", response_model=ReviewResponse)
def make_decision(project_id: int, site_id: int, review_id: int, payload: ReviewDecisionUpdate, db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    review.decision = payload.decision
    review.comments = payload.comments
    db.commit()
    db.refresh(review)

    log_event(
        db,
        project_id=project_id,
        action="review_decision",
        object_type="review",
        object_id=str(review.id),
        details={"decision": payload.decision, "reviewer": review.reviewer_id},
    )
    db.commit()

    return review


@router.get("/{version_id}/reviews", response_model=list[ReviewResponse])
def list_reviews(project_id: int, site_id: int, version_id: int, db: Session = Depends(get_db)):
    get_design_version_or_404(project_id, site_id, version_id, db)
    return db.query(Review).filter(Review.design_version_id == version_id).order_by(Review.id.desc()).all()
