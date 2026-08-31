import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_site():
    project = client.post(
        "/api/v1/projects",
        json={"name": "Design Project", "location": "Dadu"},
    ).json()["id"]

    site = client.post(
        f"/api/v1/projects/{project}/sites",
        json={"name": "Site A"},
    ).json()["id"]

    return project, site


def url(project, site):
    return (
        f"/api/v1/projects/{project}/sites/{site}"
        "/design-specification"
    )


def valid_payload():
    return {
        "family_size": 6,
        "shelter_type": "temporary",
        "required_spaces": [
            "sleeping",
            "circulation",
            "entrance",
        ],
        "maximum_footprint_m2": 25,
        "maximum_height_m": 3.5,
        "available_materials": [
            "bamboo",
            "corrugated_metal",
        ],
        "preferred_materials": [
            "bamboo",
        ],
        "priorities": [
            "site_fit",
            "material_efficiency",
        ],
        "coordinator_notes": "Prioritize simple assembly.",
    }


def test_specification_not_found_initially():
    p, s = setup_site()
    assert client.get(url(p, s)).status_code == 404


def test_create_specification():
    p, s = setup_site()

    r = client.put(url(p, s), json=valid_payload())

    assert r.status_code == 200
    assert r.json()["site_id"] == s
    assert r.json()["status"] == "draft"

    stored = json.loads(r.json()["specification_json"])

    assert stored["family_size"] == 6
    assert stored["maximum_footprint_m2"] == 25
    assert stored["preferred_materials"] == ["bamboo"]


def test_update_specification_resets_to_draft():
    p, s = setup_site()

    client.put(url(p, s), json=valid_payload())
    assert client.post(f"{url(p, s)}/ready").status_code == 200

    changed = valid_payload()
    changed["family_size"] = 8

    r = client.put(url(p, s), json=changed)

    assert r.status_code == 200
    assert r.json()["status"] == "draft"


def test_ready_specification():
    p, s = setup_site()

    client.put(url(p, s), json=valid_payload())

    r = client.post(f"{url(p, s)}/ready")

    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_family_size_required():
    p, s = setup_site()

    payload = valid_payload()
    payload["family_size"] = 0

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 422


def test_family_size_has_reasonable_upper_bound():
    p, s = setup_site()

    payload = valid_payload()
    payload["family_size"] = 51

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 422


def test_invalid_shelter_type_rejected():
    p, s = setup_site()

    payload = valid_payload()
    payload["shelter_type"] = "permanent_house"

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 422


def test_negative_footprint_rejected():
    p, s = setup_site()

    payload = valid_payload()
    payload["maximum_footprint_m2"] = -1

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 422


def test_zero_height_rejected():
    p, s = setup_site()

    payload = valid_payload()
    payload["maximum_height_m"] = 0

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 422


def test_duplicate_list_items_are_cleaned():
    p, s = setup_site()

    payload = valid_payload()
    payload["available_materials"] = [
        "bamboo",
        "bamboo",
        " corrugated_metal ",
    ]

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 200
    stored = json.loads(r.json()["specification_json"])

    assert stored["available_materials"] == [
        "bamboo",
        "corrugated_metal",
    ]


def test_duplicate_priorities_rejected():
    p, s = setup_site()

    payload = valid_payload()
    payload["priorities"] = [
        "site_fit",
        "site_fit",
    ]

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 422


def test_extra_fields_rejected():
    p, s = setup_site()

    payload = valid_payload()
    payload["structural_safety"] = True

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 422


def test_wrong_project_cannot_access_specification():
    p1, s1 = setup_site()
    p2, _ = setup_site()

    client.put(url(p1, s1), json=valid_payload())

    r = client.get(url(p2, s1))

    assert r.status_code == 404


def test_specification_does_not_contain_engineering_verdict():
    p, s = setup_site()

    payload = valid_payload()
    payload["coordinator_notes"] = "Generate candidate design."

    r = client.put(url(p, s), json=payload)

    assert r.status_code == 200

    stored = json.loads(r.json()["specification_json"])

    assert "structural_safety" not in stored
    assert "load_capacity" not in stored
    assert "wind_resistance" not in stored
    assert "engineering_approval" not in stored
