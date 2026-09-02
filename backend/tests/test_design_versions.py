
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_ready_site():
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "Design Version Test",
            "location": "Dadu",
        },
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    site = client.post(
        f"/api/v1/projects/{project_id}/sites",
        json={"name": "Test Site"},
    )
    assert site.status_code == 201
    site_id = site.json()["id"]

    profile_url = (
        f"/api/v1/projects/{project_id}/sites/{site_id}/profile"
    )

    r = client.put(
        profile_url,
        json={
            "terrain": ["flat_ground"],
            "materials": ["bamboo"],
            "geometry": {
                "estimated_usable_area_m2": 30,
            },
        },
    )
    assert r.status_code == 200

    r = client.post(f"{profile_url}/ready")
    assert r.status_code == 200

    specification_url = (
        f"/api/v1/projects/{project_id}/sites/{site_id}"
        "/design-specification"
    )

    r = client.put(
        specification_url,
        json={
            "family_size": 6,
            "shelter_type": "temporary",
            "required_spaces": ["sleeping", "entrance"],
            "maximum_footprint_m2": 25,
            "maximum_height_m": 3.5,
            "available_materials": ["bamboo"],
            "preferred_materials": ["bamboo"],
            "priorities": [
                "site_fit",
                "material_efficiency",
            ],
        },
    )
    assert r.status_code == 200

    r = client.post(f"{specification_url}/ready")
    assert r.status_code == 200

    return project_id, site_id


def candidate_url(project_id, site_id):
    return (
        f"/api/v1/projects/{project_id}/sites/"
        f"{site_id}/design-candidates"
    )


def design_version_url(project_id, site_id):
    return (
        f"/api/v1/projects/{project_id}/sites/"
        f"{site_id}/design-versions"
    )


def test_create_design_version_from_candidate():
    project_id, site_id = setup_ready_site()

    candidate = client.post(
        f"{candidate_url(project_id, site_id)}/generate"
    )

    assert candidate.status_code == 201

    candidate_id = candidate.json()["id"]

    response = client.post(
        f"{design_version_url(project_id, site_id)}/from-candidate/"
        f"{candidate_id}"
    )

    assert response.status_code == 201

    data = response.json()

    assert data["site_id"] == site_id
    assert data["source_candidate_id"] == candidate_id
    assert data["version"] == "1.0.0"
    assert data["status"] == "draft"


def test_design_version_preserves_candidate_definition():
    project_id, site_id = setup_ready_site()

    candidate = client.post(
        f"{candidate_url(project_id, site_id)}/generate"
    )

    assert candidate.status_code == 201

    candidate_id = candidate.json()["id"]

    response = client.post(
        f"{design_version_url(project_id, site_id)}/from-candidate/"
        f"{candidate_id}"
    )

    assert response.status_code == 201

    data = response.json()

    assert data["design_json"]
    assert data["source_candidate_id"] == candidate_id


def test_design_version_requires_existing_candidate():
    project_id, site_id = setup_ready_site()

    response = client.post(
        f"{design_version_url(project_id, site_id)}/from-candidate/999999"
    )

    assert response.status_code == 404


def test_design_version_is_not_a_safety_verdict():
    project_id, site_id = setup_ready_site()

    candidate = client.post(
        f"{candidate_url(project_id, site_id)}/generate"
    )

    candidate_id = candidate.json()["id"]

    response = client.post(
        f"{design_version_url(project_id, site_id)}/from-candidate/"
        f"{candidate_id}"
    )

    assert response.status_code == 201

    data = response.json()

    assert "safe" not in data
    assert "validation_status" not in data
    assert "approval" not in data