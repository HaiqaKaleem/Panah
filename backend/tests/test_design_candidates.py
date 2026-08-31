import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_ready_site():
    p = client.post(
        "/api/v1/projects",
        json={"name": "Generation Project", "location": "Dadu"},
    ).json()["id"]

    s = client.post(
        f"/api/v1/projects/{p}/sites",
        json={"name": "Site A"},
    ).json()["id"]

    profile_url = f"/api/v1/projects/{p}/sites/{s}/profile"

    client.put(
        profile_url,
        json={
            "terrain": ["uneven_ground"],
            "materials": ["bamboo"],
            "geometry": {"estimated_usable_area_m2": 30},
        },
    )

    client.post(f"{profile_url}/ready")

    spec_url = (
        f"/api/v1/projects/{p}/sites/{s}"
        "/design-specification"
    )

    client.put(
        spec_url,
        json={
            "family_size": 6,
            "shelter_type": "temporary",
            "required_spaces": ["sleeping", "entrance"],
            "maximum_footprint_m2": 25,
            "maximum_height_m": 3.5,
            "available_materials": ["bamboo"],
            "preferred_materials": ["bamboo"],
            "priorities": ["site_fit", "material_efficiency"],
        },
    )

    client.post(f"{spec_url}/ready")

    return p, s


def candidate_url(p, s):
    return f"/api/v1/projects/{p}/sites/{s}/design-candidates"


def test_generation_requires_ready_profile():
    p = client.post(
        "/api/v1/projects",
        json={"name": "Not Ready", "location": "Dadu"},
    ).json()["id"]

    s = client.post(
        f"/api/v1/projects/{p}/sites",
        json={"name": "Site"},
    ).json()["id"]

    profile_url = f"/api/v1/projects/{p}/sites/{s}/profile"
    client.put(profile_url, json={"terrain": ["muddy_ground"]})

    spec_url = (
        f"/api/v1/projects/{p}/sites/{s}"
        "/design-specification"
    )

    client.put(
        spec_url,
        json={"family_size": 4},
    )
    client.post(f"{spec_url}/ready")

    r = client.post(f"{candidate_url(p,s)}/generate")

    assert r.status_code == 422


def test_generation_requires_ready_specification():
    p = client.post(
        "/api/v1/projects",
        json={"name": "Not Ready Spec", "location": "Dadu"},
    ).json()["id"]

    s = client.post(
        f"/api/v1/projects/{p}/sites",
        json={"name": "Site"},
    ).json()["id"]

    profile_url = f"/api/v1/projects/{p}/sites/{s}/profile"
    client.put(profile_url, json={"terrain": ["flat_ground"]})
    client.post(f"{profile_url}/ready")

    client.put(
        f"/api/v1/projects/{p}/sites/{s}/design-specification",
        json={"family_size": 4},
    )

    r = client.post(f"{candidate_url(p,s)}/generate")

    assert r.status_code == 422


def test_generate_candidate():
    p, s = setup_ready_site()

    r = client.post(f"{candidate_url(p,s)}/generate")

    assert r.status_code == 201

    data = r.json()

    assert data["site_id"] == s
    assert data["status"] == "generated"
    assert data["generator_name"] == "mock-parametric-generator"

    candidate = json.loads(data["candidate_json"])

    assert candidate["footprint_m2"] > 0
    assert candidate["overall_height_m"] > 0
    assert len(candidate["components"]) >= 1


def test_candidate_has_input_snapshot():
    p, s = setup_ready_site()

    r = client.post(f"{candidate_url(p,s)}/generate")
    snapshot = json.loads(r.json()["input_snapshot_json"])

    assert "site_profile" in snapshot
    assert "design_specification" in snapshot
    assert snapshot["design_specification"]["family_size"] == 6


def test_candidate_contains_no_safety_verdict():
    p, s = setup_ready_site()

    r = client.post(f"{candidate_url(p,s)}/generate")
    candidate = json.loads(r.json()["candidate_json"])

    assert "safe" not in candidate
    assert "structural_safety" not in candidate
    assert "load_capacity" not in candidate
    assert "wind_resistance" not in candidate


def test_list_candidates():
    p, s = setup_ready_site()

    client.post(f"{candidate_url(p,s)}/generate")
    client.post(f"{candidate_url(p,s)}/generate")

    r = client.get(candidate_url(p,s))

    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_candidate():
    p, s = setup_ready_site()

    created = client.post(f"{candidate_url(p,s)}/generate").json()
    cid = created["id"]

    r = client.get(f"{candidate_url(p,s)}/{cid}")

    assert r.status_code == 200
    assert r.json()["id"] == cid


def test_select_candidate():
    p, s = setup_ready_site()

    created = client.post(f"{candidate_url(p,s)}/generate").json()
    cid = created["id"]

    r = client.patch(
        f"{candidate_url(p,s)}/{cid}/status?status=selected"
    )

    assert r.status_code == 200
    assert r.json()["status"] == "selected"


def test_reject_candidate():
    p, s = setup_ready_site()

    created = client.post(f"{candidate_url(p,s)}/generate").json()
    cid = created["id"]

    r = client.patch(
        f"{candidate_url(p,s)}/{cid}/status?status=rejected"
    )

    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_invalid_candidate_status():
    p, s = setup_ready_site()

    created = client.post(f"{candidate_url(p,s)}/generate").json()
    cid = created["id"]

    r = client.patch(
        f"{candidate_url(p,s)}/{cid}/status?status=approved"
    )

    assert r.status_code == 422
