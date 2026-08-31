from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_valid():
    r = client.post(
        "/api/v1/projects",
        json={"name": "Bug Test", "location": "Dadu"},
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_patch_null_name_returns_422():
    pid = create_valid()
    r = client.patch(f"/api/v1/projects/{pid}", json={"name": None})
    assert r.status_code == 422


def test_patch_null_location_returns_422():
    pid = create_valid()
    r = client.patch(f"/api/v1/projects/{pid}", json={"location": None})
    assert r.status_code == 422


def test_create_numeric_name_returns_422():
    r = client.post(
        "/api/v1/projects",
        json={"name": 123, "location": "Dadu"},
    )
    assert r.status_code == 422


def test_create_numeric_location_returns_422():
    r = client.post(
        "/api/v1/projects",
        json={"name": "Dadu", "location": 123},
    )
    assert r.status_code == 422


def test_update_numeric_name_returns_422():
    pid = create_valid()
    r = client.patch(f"/api/v1/projects/{pid}", json={"name": 123})
    assert r.status_code == 422


def test_update_numeric_location_returns_422():
    pid = create_valid()
    r = client.patch(f"/api/v1/projects/{pid}", json={"location": 123})
    assert r.status_code == 422
