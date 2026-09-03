from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _constraint_set_payload():
    return {
        "version": "CS-001",
        "occupancy": {"people": 6},
        "site": {"length_m": 6, "width_m": 5},
        "materials": [
            {
                "id": "MAT-BAM-01",
                "type": "treated_bamboo",
                "qty": 120,
                "length_m": 3,
                "diameter_m": 0.12,
            }
        ],
        "environment": {"scenario": "monsoon_lowland"},
        "design_target": "roof_truss",
    }


def _setup_site():
    project_id = client.post(
        "/api/v1/projects",
        json={"name": "Pipeline Project", "location": "Lahore"},
    ).json()["id"]

    site_id = client.post(
        f"/api/v1/projects/{project_id}/sites",
        json={"name": "Pipeline Site"},
    ).json()["id"]

    return project_id, site_id


def test_create_and_fetch_constraint_set():
    project_id, site_id = _setup_site()

    response = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets",
        json=_constraint_set_payload(),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["site_id"] == site_id
    assert body["constraints"]["materials"][0]["id"] == "MAT-BAM-01"

    fetched = client.get(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets/{body['id']}"
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_generate_produces_three_candidates_with_mixed_compliance():
    project_id, site_id = _setup_site()

    cs = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets",
        json=_constraint_set_payload(),
    ).json()

    response = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets/{cs['id']}/generate",
        json={"count": 3},
    )
    assert response.status_code == 201
    summaries = response.json()
    assert len(summaries) == 3

    # The direct/site-sized candidate is expected to fail; the
    # material-constrained candidates are expected to pass.
    compliance_by_candidate = {s["candidate_id"]: s["compliant"] for s in summaries}
    assert compliance_by_candidate["LOCAL-01"] is False
    assert compliance_by_candidate["LOCAL-02"] is True
    assert compliance_by_candidate["LOCAL-03"] is True


def test_generated_design_detail_contains_design_analysis_and_rules():
    project_id, site_id = _setup_site()

    cs = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets",
        json=_constraint_set_payload(),
    ).json()

    summaries = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets/{cs['id']}/generate",
        json={"count": 1},
    ).json()

    design_id = summaries[0]["id"]
    detail = client.get(
        f"/api/v1/projects/{project_id}/sites/{site_id}/generated-designs/{design_id}"
    )
    assert detail.status_code == 200
    body = detail.json()
    assert "design" in body and "analysis" in body and "rules" in body
    assert body["design"]["members"]
    assert body["rules"]["summary"]["total"] == 6


def test_generated_design_status_can_be_updated():
    project_id, site_id = _setup_site()

    cs = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets",
        json=_constraint_set_payload(),
    ).json()

    summaries = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets/{cs['id']}/generate",
        json={"count": 1},
    ).json()

    design_id = summaries[0]["id"]
    update = client.patch(
        f"/api/v1/projects/{project_id}/sites/{site_id}/generated-designs/{design_id}/status",
        params={"status_value": "selected"},
    )
    assert update.status_code == 200
    assert update.json()["status"] == "selected"


def test_unknown_constraint_set_returns_404():
    project_id, site_id = _setup_site()

    response = client.get(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets/999999"
    )
    assert response.status_code == 404
