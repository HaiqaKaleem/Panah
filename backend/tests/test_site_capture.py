from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_project():
    r = client.post(
        "/api/v1/projects",
        json={
            "name": "Site Test Project",
            "location": "Dadu, Sindh",
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


def create_site(project_id):
    r = client.post(
        f"/api/v1/projects/{project_id}/sites",
        json={
            "name": "Site A",
            "latitude": 26.730,
            "longitude": 67.776,
        },
    )
    assert r.status_code == 201
    return r.json()


def test_create_site():
    project_id = create_project()
    site = create_site(project_id)

    assert site["project_id"] == project_id
    assert site["name"] == "Site A"
    assert site["latitude"] == 26.730
    assert site["longitude"] == 67.776
    assert site["status"] == "capture_pending"


def test_list_sites_is_project_scoped():
    p1 = create_project()
    p2 = create_project()

    s1 = create_site(p1)
    s2 = create_site(p2)

    r1 = client.get(f"/api/v1/projects/{p1}/sites")
    r2 = client.get(f"/api/v1/projects/{p2}/sites")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert any(s["id"] == s1["id"] for s in r1.json())
    assert not any(s["id"] == s2["id"] for s in r1.json())


def test_site_cannot_be_accessed_through_wrong_project():
    p1 = create_project()
    p2 = create_project()
    site = create_site(p1)

    r = client.get(f"/api/v1/projects/{p2}/sites/{site['id']}")
    assert r.status_code == 404


def test_create_capture():
    project_id = create_project()
    site = create_site(project_id)

    captured = "2026-08-22T10:30:00Z"

    r = client.post(
        f"/api/v1/projects/{project_id}/sites/{site['id']}/captures",
        json={
            "captured_at": captured,
            "latitude": 26.7301,
            "longitude": 67.7761,
            "notes": "Initial field walkthrough",
        },
    )

    assert r.status_code == 201
    data = r.json()
    assert data["site_id"] == site["id"]
    assert data["latitude"] == 26.7301
    assert data["longitude"] == 67.7761
    assert data["notes"] == "Initial field walkthrough"


def test_capture_changes_site_status():
    project_id = create_project()
    site = create_site(project_id)

    client.post(
        f"/api/v1/projects/{project_id}/sites/{site['id']}/captures",
        json={
            "captured_at": "2026-08-22T10:30:00Z",
        },
    )

    r = client.get(f"/api/v1/projects/{project_id}/sites/{site['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "capture_uploaded"


def test_list_captures_is_site_scoped():
    project_id = create_project()
    s1 = create_site(project_id)
    s2 = create_site(project_id)

    for site in (s1, s2):
        r = client.post(
            f"/api/v1/projects/{project_id}/sites/{site['id']}/captures",
            json={"captured_at": "2026-08-22T10:30:00Z"},
        )
        assert r.status_code == 201

    r = client.get(
        f"/api/v1/projects/{project_id}/sites/{s1['id']}/captures"
    )
    assert r.status_code == 200
    assert all(c["site_id"] == s1["id"] for c in r.json())


def test_capture_wrong_site_returns_404():
    project_id = create_project()
    s1 = create_site(project_id)
    s2 = create_site(project_id)

    created = client.post(
        f"/api/v1/projects/{project_id}/sites/{s1['id']}/captures",
        json={"captured_at": "2026-08-22T10:30:00Z"},
    )
    capture_id = created.json()["id"]

    r = client.get(
        f"/api/v1/projects/{project_id}/sites/{s2['id']}/captures/{capture_id}"
    )
    assert r.status_code == 404


def test_invalid_site_coordinates_are_rejected():
    project_id = create_project()

    r = client.post(
        f"/api/v1/projects/{project_id}/sites",
        json={
            "name": "Bad",
            "latitude": 100,
            "longitude": 200,
        },
    )
    assert r.status_code == 422


def test_unknown_site_fields_are_rejected():
    project_id = create_project()

    r = client.post(
        f"/api/v1/projects/{project_id}/sites",
        json={
            "name": "Site",
            "unexpected": "field",
        },
    )
    assert r.status_code == 422


def test_unknown_capture_fields_are_rejected():
    project_id = create_project()
    site = create_site(project_id)

    r = client.post(
        f"/api/v1/projects/{project_id}/sites/{site['id']}/captures",
        json={
            "captured_at": "2026-08-22T10:30:00Z",
            "unexpected": "field",
        },
    )
    assert r.status_code == 422
