"""
End-to-end pipeline test.

Exercises the complete Panah workflow:
    Project → Site → Constraint Set → Generate → Validate → Promote → Review

This proves the full hackathon demo flow works.
"""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_full_pipeline():
    # --- 1. Create Project ---
    resp = client.post("/api/v1/projects", json={
        "name": "E2E Test Shelter",
        "location": "Islamabad, Pakistan",
    })
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]

    # --- 2. Create Site ---
    resp = client.post(f"/api/v1/projects/{project_id}/sites", json={
        "name": "Test Site Alpha",
        "latitude": 33.6844,
        "longitude": 73.0479,
    })
    assert resp.status_code == 201
    site = resp.json()
    site_id = site["id"]

    # --- 3. Create Constraint Set ---
    constraint_payload = {
        "schema_version": "1.0.0",
        "version": "CS-E2E-001",
        "occupancy": {"people": 5},
        "site": {"length_m": 6.0, "width_m": 5.0},
        "materials": [
            {
                "id": "MAT-BAM-01",
                "type": "treated_bamboo",
                "qty": 20,
                "length_m": 3.0,
                "diameter_m": 0.08,
            },
            {
                "id": "MAT-TIM-01",
                "type": "reclaimed_timber",
                "qty": 10,
                "length_m": 2.5,
                "diameter_m": 0.1,
            },
        ],
        "environment": {"scenario": "semi-arid, moderate wind zone"},
        "design_target": "roof_truss",
        "unknowns": [],
    }
    resp = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets",
        json=constraint_payload,
    )
    assert resp.status_code == 201
    cs = resp.json()
    cs_id = cs["id"]

    # --- 4. Generate Designs from Constraint Set ---
    resp = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/constraint-sets/{cs_id}/generate",
        json={"count": 2},
    )
    assert resp.status_code == 201
    designs = resp.json()
    assert len(designs) == 2

    first_design = designs[0]
    design_id = first_design["id"]

    # Check the summary has expected fields
    assert "overall_integrity_score" in first_design
    assert "compliant" in first_design
    assert "score" in first_design

    # --- 5. Get Generated Design Detail ---
    resp = client.get(
        f"/api/v1/projects/{project_id}/sites/{site_id}/generated-designs/{design_id}",
    )
    assert resp.status_code == 200
    detail = resp.json()
    assert "design" in detail
    assert "analysis" in detail
    assert "rules" in detail

    # --- 6. Validate Generated Design (full pipeline) ---
    resp = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/generated-designs/{design_id}/validate",
    )
    assert resp.status_code == 201
    validation = resp.json()
    assert "analysis" in validation
    assert "rules" in validation
    assert "compliance" in validation
    assert validation["compliance"]["status"] in ("pass", "review", "fail")

    # --- 7. Promote to Design Version ---
    resp = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/generated-designs/{design_id}/promote",
    )
    assert resp.status_code == 201
    dv = resp.json()
    dv_id = dv["id"]
    assert dv["version"] == first_design["version"]
    assert dv["promoted_from"] == design_id

    # --- 8. Submit Review ---
    resp = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/design-versions/{dv_id}/submit-review",
        json={"reviewer_id": "engineer-ahmed"},
    )
    assert resp.status_code == 201
    review = resp.json()
    review_id = review["id"]
    assert review["decision"] == "pending"

    # --- 9. Make Review Decision ---
    resp = client.post(
        f"/api/v1/projects/{project_id}/sites/{site_id}/design-versions/reviews/{review_id}/decision",
        json={
            "decision": "approve",
            "comments": "Structural analysis passes all Sphere requirements. Approved for construction.",
        },
    )
    assert resp.status_code == 200
    decision = resp.json()
    assert decision["decision"] == "approve"
    assert "Sphere" in decision["comments"]

    # --- 10. Verify Audit Trail ---
    resp = client.get(
        f"/api/v1/audit?project_id={project_id}",
    )
    assert resp.status_code == 200
    audit = resp.json()
    actions = [e["action"] for e in audit]
    assert "generated_design_validated" in actions
    assert "generated_design_promoted" in actions
    assert "review_submitted" in actions
    assert "review_decision" in actions

    # --- 11. Dashboard Stats ---
    resp = client.get(f"/api/v1/projects/{project_id}/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["site_count"] >= 1
    assert stats["generated_design_count"] >= 2

    # --- 12. Global Dashboard ---
    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    global_stats = resp.json()
    assert global_stats["total_projects"] >= 1

    # --- 13. Project History ---
    resp = client.get("/api/v1/projects-history")
    assert resp.status_code == 200
    history = resp.json()
    assert history["count"] >= 1

    # --- 14. Standards Rules ---
    resp = client.get("/api/v1/standards/rules")
    assert resp.status_code == 200
    rules = resp.json()
    assert rules["count"] == 6
    assert rules["standard"] == "Sphere Handbook"

    # --- 15. Material Catalog ---
    resp = client.get("/api/v1/material-catalog")
    assert resp.status_code == 200
    catalog = resp.json()
    assert catalog["count"] >= 4
    assert "categories" in catalog

    # --- 16. Materials Summary ---
    resp = client.get(f"/api/v1/projects/{project_id}/materials-summary")
    assert resp.status_code == 200

    # --- 17. Health Check ---
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # --- 18. Root ---
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["version"] == "1.0.0"


def test_material_catalog_filtering():
    """Test material catalog filtering and sorting."""
    resp = client.get("/api/v1/material-catalog?category=Structural")
    assert resp.status_code == 200
    data = resp.json()
    for mat in data["materials"]:
        assert mat["category"] == "Structural"

    resp = client.get("/api/v1/material-catalog?sort_by=lifespan")
    assert resp.status_code == 200
    lifespans = [m["expected_lifespan_years"] for m in resp.json()["materials"]]
    assert lifespans == sorted(lifespans)

    resp = client.get("/api/v1/material-catalog?min_lifespan_years=15")
    assert resp.status_code == 200
    for mat in resp.json()["materials"]:
        assert mat["expected_lifespan_years"] >= 15


def test_standards_categories():
    """Test standards categories endpoint."""
    resp = client.get("/api/v1/standards/categories")
    assert resp.status_code == 200
    cats = resp.json()["categories"]
    category_names = [c["category"] for c in cats]
    assert "wind" in category_names
    assert "snow" in category_names
    assert "materials" in category_names


def test_dashboard_increments():
    """Test that dashboard stats increment after creating a project."""
    resp_before = client.get("/api/v1/dashboard/stats")
    count_before = resp_before.json()["total_projects"]

    client.post("/api/v1/projects", json={
        "name": "Dashboard Count Test",
        "location": "Lahore",
    })

    resp_after = client.get("/api/v1/dashboard/stats")
    assert resp_after.json()["total_projects"] == count_before + 1


def test_duplicate_promote_rejected():
    """Test that promoting the same design twice returns 409."""
    # Create project + site + constraint set + generate
    resp = client.post("/api/v1/projects", json={"name": "Dup Test", "location": "Test"})
    pid = resp.json()["id"]

    resp = client.post(f"/api/v1/projects/{pid}/sites", json={"name": "Dup Site"})
    sid = resp.json()["id"]

    cs_payload = {
        "schema_version": "1.0.0",
        "version": "CS-DUP-001",
        "occupancy": {"people": 3},
        "site": {"length_m": 4.0, "width_m": 3.0},
        "materials": [
            {"id": "M1", "type": "treated_bamboo", "qty": 10, "length_m": 2.0, "diameter_m": 0.06},
        ],
        "environment": {"scenario": "tropical"},
        "design_target": "roof_truss",
    }
    resp = client.post(f"/api/v1/projects/{pid}/sites/{sid}/constraint-sets", json=cs_payload)
    csid = resp.json()["id"]

    resp = client.post(f"/api/v1/projects/{pid}/sites/{sid}/constraint-sets/{csid}/generate", json={"count": 1})
    did = resp.json()[0]["id"]

    # First promote — should succeed
    resp = client.post(f"/api/v1/projects/{pid}/sites/{sid}/generated-designs/{did}/promote")
    assert resp.status_code == 201

    # Second promote — should fail with 409
    resp = client.post(f"/api/v1/projects/{pid}/sites/{sid}/generated-designs/{did}/promote")
    assert resp.status_code == 409
