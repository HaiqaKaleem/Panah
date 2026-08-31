import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storage.factory import get_media_storage

client = TestClient(app)


def setup_capture():
    p = client.post(
        "/api/v1/projects",
        json={"name": "Media Project", "location": "Dadu"},
    )
    project_id = p.json()["id"]

    s = client.post(
        f"/api/v1/projects/{project_id}/sites",
        json={"name": "Site A"},
    )
    site_id = s.json()["id"]

    c = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/captures",
        json={"captured_at": "2026-08-22T10:30:00Z"},
    )
    capture_id = c.json()["id"]

    return project_id, site_id, capture_id


def media_url(project_id, site_id, capture_id):
    return (
        f"/api/v1/projects/{project_id}/sites/"
        f"{site_id}/captures/{capture_id}/media"
    )


def test_upload_photo():
    p, s, c = setup_capture()
    content = b"fake-jpeg-content"

    r = client.post(
        media_url(p, s, c),
        files={"file": ("site.jpg", content, "image/jpeg")},
        data={
            "captured_at": "2026-08-22T10:31:00Z",
            "latitude": "26.7301",
            "longitude": "67.7761",
        },
    )

    assert r.status_code == 201
    data = r.json()
    assert data["media_type"] == "photo"
    assert data["mime_type"] == "image/jpeg"
    assert data["file_size"] == len(content)
    assert data["sha256"] == hashlib.sha256(content).hexdigest()

    storage_root = get_media_storage().root / "captures" / str(c)
    assert any(storage_root.iterdir())


def test_upload_video():
    p, s, c = setup_capture()

    r = client.post(
        media_url(p, s, c),
        files={"file": ("walkthrough.mp4", b"video-content", "video/mp4")},
    )

    assert r.status_code == 201
    assert r.json()["media_type"] == "video"


def test_list_media():
    p, s, c = setup_capture()

    client.post(
        media_url(p, s, c),
        files={"file": ("a.jpg", b"a", "image/jpeg")},
    )
    client.post(
        media_url(p, s, c),
        files={"file": ("b.jpg", b"b", "image/jpeg")},
    )

    r = client.get(media_url(p, s, c))
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_media():
    p, s, c = setup_capture()

    created = client.post(
        media_url(p, s, c),
        files={"file": ("a.jpg", b"a", "image/jpeg")},
    )
    media_id = created.json()["id"]

    r = client.get(f"{media_url(p, s, c)}/{media_id}")
    assert r.status_code == 200
    assert r.json()["id"] == media_id


def test_wrong_capture_cannot_access_media():
    p, s, c1 = setup_capture()

    c2 = client.post(
        f"/api/v1/projects/{p}/sites/{s}/captures",
        json={"captured_at": "2026-08-22T11:00:00Z"},
    ).json()["id"]

    created = client.post(
        media_url(p, s, c1),
        files={"file": ("a.jpg", b"a", "image/jpeg")},
    )
    media_id = created.json()["id"]

    r = client.get(f"{media_url(p, s, c2)}/{media_id}")
    assert r.status_code == 404


def test_unsupported_type_rejected():
    p, s, c = setup_capture()

    r = client.post(
        media_url(p, s, c),
        files={"file": ("bad.exe", b"bad", "application/octet-stream")},
    )
    assert r.status_code == 415


def test_duplicate_content_rejected():
    p, s, c = setup_capture()
    content = b"same-content"

    first = client.post(
        media_url(p, s, c),
        files={"file": ("a.jpg", content, "image/jpeg")},
    )
    assert first.status_code == 201

    second = client.post(
        media_url(p, s, c),
        files={"file": ("different-name.jpg", content, "image/jpeg")},
    )
    assert second.status_code == 409


def test_invalid_coordinates_rejected():
    p, s, c = setup_capture()

    r = client.post(
        media_url(p, s, c),
        files={"file": ("a.jpg", b"a", "image/jpeg")},
        data={"latitude": "100"},
    )
    assert r.status_code == 422


def test_nonexistent_capture_rejected():
    p, s, c = setup_capture()

    r = client.post(
        media_url(p, s, 999999),
        files={"file": ("a.jpg", b"a", "image/jpeg")},
    )
    assert r.status_code == 404


def test_storage_key_cannot_escape_root():
    storage = get_media_storage()

    try:
        storage.get_path("../../outside.txt")
        assert False, "Expected invalid storage key"
    except ValueError:
        pass
