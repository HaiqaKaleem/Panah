from io import BytesIO
import json

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.models.media import Media
from app.core.database import get_db

client = TestClient(app)


def setup_capture():
    p = client.post(
        "/api/v1/projects",
        json={"name": "Metadata Project", "location": "Dadu"},
    )
    pid = p.json()["id"]

    s = client.post(
        f"/api/v1/projects/{pid}/sites",
        json={"name": "Site A"},
    )
    sid = s.json()["id"]

    c = client.post(
        f"/api/v1/projects/{pid}/sites/{sid}/captures",
        json={"captured_at": "2026-08-22T10:30:00Z"},
    )
    return pid, sid, c.json()["id"]


def media_url(p, s, c):
    return f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media"


def jpeg_bytes(width=640, height=480):
    image = Image.new("RGB", (width, height), "white")
    buf = BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def get_media(media_id):
    db = next(get_db())
    return db.get(Media, media_id)


def test_image_dimensions_extracted():
    p, s, c = setup_capture()
    r = client.post(
        media_url(p, s, c),
        files={"file": ("site.jpg", jpeg_bytes(), "image/jpeg")},
    )
    assert r.status_code == 201

    metadata = json.loads(get_media(r.json()["id"]).metadata_json)
    assert metadata["extraction_status"] == "complete"
    assert metadata["technical"]["width"] == 640
    assert metadata["technical"]["height"] == 480
    assert metadata["technical"]["format"] == "JPEG"


def test_corrupt_image_does_not_fail_upload():
    p, s, c = setup_capture()
    content = b"not-really-a-jpeg"

    r = client.post(
        media_url(p, s, c),
        files={"file": ("broken.jpg", content, "image/jpeg")},
    )
    assert r.status_code == 201

    media_id = r.json()["id"]
    metadata = json.loads(get_media(media_id).metadata_json)

    assert metadata["extraction_status"] == "failed"

    original = client.get(f"{media_url(p,s,c)}/{media_id}/file")
    assert original.status_code == 200
    assert original.content == content


def test_video_upload_survives_optional_reader_failure():
    p, s, c = setup_capture()

    r = client.post(
        media_url(p, s, c),
        files={"file": ("walkthrough.mp4", b"not-a-real-video", "video/mp4")},
    )
    assert r.status_code == 201

    media_id = r.json()["id"]
    original = client.get(f"{media_url(p,s,c)}/{media_id}/file")

    assert original.status_code == 200
    assert original.content == b"not-a-real-video"


def test_metadata_does_not_modify_original():
    p, s, c = setup_capture()
    content = jpeg_bytes(320, 240)

    r = client.post(
        media_url(p, s, c),
        files={"file": ("site.jpg", content, "image/jpeg")},
    )
    media_id = r.json()["id"]

    original = client.get(f"{media_url(p,s,c)}/{media_id}/file")
    assert original.content == content


def test_metadata_is_not_ai_analysis():
    p, s, c = setup_capture()

    r = client.post(
        media_url(p, s, c),
        files={"file": ("site.jpg", jpeg_bytes(), "image/jpeg")},
    )
    metadata = json.loads(get_media(r.json()["id"]).metadata_json)

    assert "observations" not in metadata
    assert "ai_analysis" not in metadata
