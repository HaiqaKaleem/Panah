from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_project():
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Dadu Flood Relief - Site A",
            "location": "Dadu, Sindh, Pakistan",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Dadu Flood Relief - Site A"
    assert data["location"] == "Dadu, Sindh, Pakistan"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_project_not_found():
    response = client.get("/api/v1/projects/999999")
    assert response.status_code == 404


def test_update_project():
    create = client.post(
        "/api/v1/projects",
        json={
            "name": "Original",
            "location": "Dadu",
        },
    )

    project_id = create.json()["id"]

    response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={
            "name": "Updated Project",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project"
