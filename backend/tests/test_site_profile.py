import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_site():
    p = client.post(
        "/api/v1/projects",
        json={"name": "Profile Project", "location": "Dadu"},
    ).json()["id"]

    s = client.post(
        f"/api/v1/projects/{p}/sites",
        json={"name": "Site A"},
    ).json()["id"]

    return p, s


def url(p, s):
    return f"/api/v1/projects/{p}/sites/{s}/profile"


def test_profile_does_not_exist_until_created():
    p, s = setup_site()
    r = client.get(url(p, s))
    assert r.status_code == 404


def test_create_profile():
    p, s = setup_site()

    payload = {
        "terrain": ["uneven_ground", "standing_water"],
        "objects": ["tree"],
        "access": ["pedestrian_path"],
        "materials": ["bamboo", "corrugated_metal"],
        "conditions": [],
        "geometry": {"estimated_usable_area_m2": 30},
    }

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 200
    assert r.json()["site_id"] == s
    assert r.json()["status"] == "draft"

    stored = json.loads(r.json()["profile_json"])
    assert stored["terrain"] == ["uneven_ground", "standing_water"]


def test_profile_can_be_updated():
    p, s = setup_site()

    client.put(
        url(p, s),
        json={"terrain": ["muddy_ground"]},
    )

    r = client.put(
        url(p, s),
        json={"terrain": ["flat_ground"], "materials": ["bamboo"]},
    )

    assert r.status_code == 200
    stored = json.loads(r.json()["profile_json"])
    assert stored["terrain"] == ["flat_ground"]
    assert stored["materials"] == ["bamboo"]


def test_empty_profile_cannot_be_ready():
    p, s = setup_site()

    client.put(url(p, s), json={})

    r = client.post(f"{url(p, s)}/ready")

    assert r.status_code == 422


def test_profile_can_be_marked_ready():
    p, s = setup_site()

    client.put(
        url(p, s),
        json={
            "terrain": ["uneven_ground"],
            "materials": ["bamboo"],
        },
    )

    r = client.post(f"{url(p, s)}/ready")

    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_wrong_project_cannot_access_profile():
    p1, s1 = setup_site()
    p2, _ = setup_site()

    client.put(
        url(p1, s1),
        json={"terrain": ["uneven_ground"]},
    )

    r = client.get(url(p2, s1))
    assert r.status_code == 404


def test_extra_fields_rejected():
    p, s = setup_site()

    r = client.put(
        url(p, s),
        json={
            "terrain": ["muddy_ground"],
            "engineering_safety": "safe",
        },
    )

    assert r.status_code == 422
