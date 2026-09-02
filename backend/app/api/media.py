import hashlib
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.capture import Capture
from app.models.media import Media
from app.metadata.extractor import extract_metadata
from app.models.site import Site
from app.storage.factory import get_media_storage

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/captures/{capture_id}/media",
    tags=["Media"],
)

ALLOWED_TYPES = {
    "image/jpeg": "photo",
    "image/png": "photo",
    "image/webp": "photo",
    "video/mp4": "video",
    "video/quicktime": "video",
    "video/webm": "video",
}

MAX_PHOTO_BYTES = 20 * 1024 * 1024
MAX_VIDEO_BYTES = 500 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def get_capture_or_404(
    project_id: int,
    site_id: int,
    capture_id: int,
    db: Session,
) -> Capture:
    site = db.get(Site, site_id)

    if site is None or site.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )

    capture = db.get(Capture, capture_id)

    if capture is None or capture.site_id != site_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capture not found",
        )

    return capture


def safe_extension(filename: str) -> str:
    # Only use the final extension as a harmless storage suffix.
    # The actual stored filename is a generated UUID.
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    allowed_extensions = {
        "jpg", "jpeg", "png", "webp",
        "mp4", "mov", "webm",
    }

    return f".{extension}" if extension in allowed_extensions else ""


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def upload_media(
    project_id: int,
    site_id: int,
    capture_id: int,
    file: UploadFile = File(...),
    captured_at: datetime | None = Form(default=None),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    db: Session = Depends(get_db),
):
    capture = get_capture_or_404(
        project_id,
        site_id,
        capture_id,
        db,
    )

    media_type = ALLOWED_TYPES.get(file.content_type or "")

    if media_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported media type",
        )

    if latitude is not None and not -90 <= latitude <= 90:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid latitude",
        )

    if longitude is not None and not -180 <= longitude <= 180:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid longitude",
        )

    max_bytes = (
        MAX_PHOTO_BYTES
        if media_type == "photo"
        else MAX_VIDEO_BYTES
    )

    # Stream the upload once, calculating its hash and size.
    hasher = hashlib.sha256()
    total_size = 0

    storage_key = (
        f"captures/{capture.id}/"
        f"{uuid.uuid4().hex}{safe_extension(file.filename or '')}"
    )

    storage = get_media_storage()

    try:
        destination = storage.root / storage_key
        destination.parent.mkdir(parents=True, exist_ok=True)

        with destination.open("wb") as output:
            while True:
                chunk = file.file.read(CHUNK_SIZE)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_bytes:
                    output.close()
                    storage.delete(storage_key)

                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Media file exceeds the size limit",
                    )

                hasher.update(chunk)
                output.write(chunk)

        digest = hasher.hexdigest()

        extracted_metadata = extract_metadata(
            destination,
            file.content_type or "application/octet-stream",
            total_size,
        )

        # Avoid creating a second record for the exact same content
        # in the same capture.
        existing = db.scalar(
            select(Media).where(
                Media.capture_id == capture.id,
                Media.sha256 == digest,
            )
        )

        if existing is not None:
            storage.delete(storage_key)

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This exact file has already been uploaded to this capture",
            )

        media = Media(
            capture_id=capture.id,
            media_type=media_type,
            original_filename=file.filename or "unnamed",
            storage_key=storage_key,
            mime_type=file.content_type or "application/octet-stream",
            file_size=total_size,
            sha256=digest,
            captured_at=captured_at,
            latitude=latitude,
            longitude=longitude,
            status="ready",
            metadata_json=json.dumps(extracted_metadata, default=str),
        )

        db.add(media)
        db.commit()
        db.refresh(media)

        return {
            "id": media.id,
            "capture_id": media.capture_id,
            "media_type": media.media_type,
            "original_filename": media.original_filename,
            "mime_type": media.mime_type,
            "file_size": media.file_size,
            "sha256": media.sha256,
            "captured_at": media.captured_at,
            "latitude": media.latitude,
            "longitude": media.longitude,
            "status": media.status,
            "created_at": media.created_at,
        }

    except HTTPException:
        raise
    except Exception:
        # Do not leave an orphaned file when database persistence fails.
        if storage.exists(storage_key):
            storage.delete(storage_key)
        raise


@router.get("")
def list_media(
    project_id: int,
    site_id: int,
    capture_id: int,
    db: Session = Depends(get_db),
):
    capture = get_capture_or_404(
        project_id,
        site_id,
        capture_id,
        db,
    )

    statement = (
        select(Media)
        .where(Media.capture_id == capture.id)
        .order_by(Media.created_at.desc())
    )

    media_items = list(db.scalars(statement).all())

    return [
        {
            "id": item.id,
            "capture_id": item.capture_id,
            "media_type": item.media_type,
            "original_filename": item.original_filename,
            "mime_type": item.mime_type,
            "file_size": item.file_size,
            "sha256": item.sha256,
            "captured_at": item.captured_at,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "status": item.status,
            "created_at": item.created_at,
        }
        for item in media_items
    ]


@router.get("/{media_id}/file")
def serve_media_file(
    project_id: int,
    site_id: int,
    capture_id: int,
    media_id: int,
    db: Session = Depends(get_db),
):
    """Serve the original uploaded file for frontend preview/playback."""
    capture = get_capture_or_404(project_id, site_id, capture_id, db)

    media = db.get(Media, media_id)

    if media is None or media.capture_id != capture.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )

    storage = get_media_storage()

    try:
        path = storage.get_path(media.storage_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    return FileResponse(
        path=path,
        media_type=media.mime_type,
        filename=media.original_filename,
        content_disposition_type="inline",
    )


@router.get("/{media_id}")
def get_media(
    project_id: int,
    site_id: int,
    capture_id: int,
    media_id: int,
    db: Session = Depends(get_db),
):
    capture = get_capture_or_404(
        project_id,
        site_id,
        capture_id,
        db,
    )

    media = db.get(Media, media_id)

    if media is None or media.capture_id != capture.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )

    return {
        "id": media.id,
        "capture_id": media.capture_id,
        "media_type": media.media_type,
        "original_filename": media.original_filename,
        "mime_type": media.mime_type,
        "file_size": media.file_size,
        "sha256": media.sha256,
        "captured_at": media.captured_at,
        "latitude": media.latitude,
        "longitude": media.longitude,
        "status": media.status,
        "created_at": media.created_at,
    }
