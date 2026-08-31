from fastapi.testclient import TestClient
from app.main import app
from app.storage.factory import get_media_storage

client = TestClient(app)

def setup_capture():
    p = client.post("/api/v1/projects", json={"name": "Serving Project", "location": "Dadu"})
    project_id = p.json()["id"]
    s = client.post(f"/api/v1/projects/{project_id}/sites", json={"name": "Site A"})
    site_id = s.json()["id"]
    c = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/captures",
        json={"captured_at": "2026-08-22T10:30:00Z"},
    )
    return project_id, site_id, c.json()["id"]

def media_url(p, s, c):
    return f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media"

def test_serve_photo():
    p, s, c = setup_capture()
    content = b"photo-original-bytes"
    created = client.post(media_url(p,s,c), files={"file": ("site.jpg", content, "image/jpeg")})
    assert created.status_code == 201
    r = client.get(f"{media_url(p,s,c)}/{created.json()['id']}/file")
    assert r.status_code == 200
    assert r.content == content
    assert r.headers["content-type"].startswith("image/jpeg")
    assert "inline" in r.headers.get("content-disposition", "")

def test_serve_video():
    p, s, c = setup_capture()
    content = b"video-original-bytes"
    created = client.post(media_url(p,s,c), files={"file": ("walkthrough.mp4", content, "video/mp4")})
    assert created.status_code == 201
    r = client.get(f"{media_url(p,s,c)}/{created.json()['id']}/file")
    assert r.status_code == 200
    assert r.content == content
    assert r.headers["content-type"].startswith("video/mp4")

def test_missing_media_returns_404():
    p, s, c = setup_capture()
    assert client.get(f"{media_url(p,s,c)}/999999/file").status_code == 404

def test_media_from_wrong_capture_returns_404():
    p, s, c1 = setup_capture()
    c2 = client.post(
        f"/api/v1/projects/{p}/sites/{s}/captures",
        json={"captured_at": "2026-08-22T11:00:00Z"},
    ).json()["id"]
    created = client.post(media_url(p,s,c1), files={"file": ("site.jpg", b"original", "image/jpeg")})
    r = client.get(f"{media_url(p,s,c2)}/{created.json()['id']}/file")
    assert r.status_code == 404

def test_missing_physical_file_returns_404():
    p, s, c = setup_capture()
    created = client.post(media_url(p,s,c), files={"file": ("site.jpg", b"original", "image/jpeg")})
    storage_root = get_media_storage().root / "captures" / str(c)
    stored_files = list(storage_root.iterdir())
    assert len(stored_files) == 1
    stored_files[0].unlink()
    r = client.get(f"{media_url(p,s,c)}/{created.json()['id']}/file")
    assert r.status_code == 404
    assert r.json()["detail"] == "Media file not found"

def test_metadata_endpoint_still_works():
    p, s, c = setup_capture()
    created = client.post(media_url(p,s,c), files={"file": ("site.jpg", b"original", "image/jpeg")})
    r = client.get(f"{media_url(p,s,c)}/{created.json()['id']}")
    assert r.status_code == 200
