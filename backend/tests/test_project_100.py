import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_project(i):
    return {
        "name": f"Test Project {i}",
        "location": f"Location {i}",
    }


# 1-10: create / response contract
@pytest.mark.parametrize("i", range(1, 11))
def test_create_project(i):
    r = client.post("/api/v1/projects", json=unique_project(i))
    assert r.status_code == 201
    data = r.json()
    assert isinstance(data["id"], int)
    assert data["name"] == f"Test Project {i}"
    assert data["location"] == f"Location {i}"
    assert data["status"] == "draft"
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)


# 11-20: get existing projects
@pytest.mark.parametrize("i", range(11, 21))
def test_get_project_after_create(i):
    created = client.post("/api/v1/projects", json=unique_project(i))
    assert created.status_code == 201
    pid = created.json()["id"]

    r = client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == pid
    assert data["name"] == f"Test Project {i}"


# 21-30: list behavior
@pytest.mark.parametrize("i", range(21, 31))
def test_list_contains_created_project(i):
    created = client.post("/api/v1/projects", json=unique_project(i))
    assert created.status_code == 201
    pid = created.json()["id"]

    r = client.get("/api/v1/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert any(p["id"] == pid for p in r.json())


# 31-40: update name
@pytest.mark.parametrize("i", range(31, 41))
def test_update_name(i):
    created = client.post("/api/v1/projects", json=unique_project(i))
    pid = created.json()["id"]

    r = client.patch(
        f"/api/v1/projects/{pid}",
        json={"name": f"Updated {i}"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == f"Updated {i}"
    assert r.json()["location"] == f"Location {i}"


# 41-50: update location
@pytest.mark.parametrize("i", range(41, 51))
def test_update_location(i):
    created = client.post("/api/v1/projects", json=unique_project(i))
    pid = created.json()["id"]

    r = client.patch(
        f"/api/v1/projects/{pid}",
        json={"location": f"New Location {i}"},
    )
    assert r.status_code == 200
    assert r.json()["location"] == f"New Location {i}"
    assert r.json()["name"] == f"Test Project {i}"


# 51-60: partial update semantics
@pytest.mark.parametrize("i", range(51, 61))
def test_partial_update_preserves_other_field(i):
    created = client.post("/api/v1/projects", json=unique_project(i))
    pid = created.json()["id"]

    r = client.patch(
        f"/api/v1/projects/{pid}",
        json={"name": f"Only Name {i}"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == f"Only Name {i}"
    assert r.json()["location"] == f"Location {i}"


# 61-70: not found
@pytest.mark.parametrize("pid", range(900001, 900011))
def test_missing_project(pid):
    r = client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Project not found"


# 71-80: invalid create payloads
@pytest.mark.parametrize("payload", [
    {},
    {"name": "", "location": "Dadu"},
    {"name": "A" * 161, "location": "Dadu"},
    {"name": "Dadu", "location": ""},
    {"name": "Dadu", "location": "L" * 161},
    {"name": None, "location": "Dadu"},
    {"name": "Dadu", "location": None},
    {"name": 123, "location": "Dadu"},
    {"name": "Dadu", "location": 123},
    {"name": ["Dadu"], "location": "Pakistan"},
])
def test_invalid_create(payload):
    r = client.post("/api/v1/projects", json=payload)
    assert r.status_code == 422


# 81-90: invalid update payloads
@pytest.mark.parametrize("payload", [
    {"name": ""},
    {"name": "A" * 161},
    {"location": ""},
    {"location": "L" * 161},
    {"name": None},
    {"location": None},
    {"name": 123},
    {"location": 123},
    {"name": ["bad"]},
    {"location": {"bad": "type"}},
])
def test_invalid_update(payload):
    created = client.post(
        "/api/v1/projects",
        json={"name": "Valid", "location": "Dadu"},
    )
    pid = created.json()["id"]

    r = client.patch(f"/api/v1/projects/{pid}", json=payload)
    assert r.status_code == 422


# 91-95: delete
@pytest.mark.parametrize("i", range(91, 96))
def test_delete_project(i):
    created = client.post("/api/v1/projects", json=unique_project(i))
    assert created.status_code == 201
    pid = created.json()["id"]

    r = client.delete(f"/api/v1/projects/{pid}")
    assert r.status_code == 204

    get = client.get(f"/api/v1/projects/{pid}")
    assert get.status_code == 404


# 96-100: repeated delete / update / malformed routes
def test_delete_missing_project():
    r = client.delete("/api/v1/projects/999991")
    assert r.status_code == 404


def test_update_missing_project():
    r = client.patch("/api/v1/projects/999992", json={"name": "Nope"})
    assert r.status_code == 404


def test_update_with_empty_object_is_allowed_as_noop():
    created = client.post(
        "/api/v1/projects",
        json={"name": "Noop", "location": "Dadu"},
    )
    pid = created.json()["id"]
    r = client.patch(f"/api/v1/projects/{pid}", json={})
    assert r.status_code == 200
    assert r.json()["name"] == "Noop"


def test_unknown_create_field_is_rejected():
    r = client.post(
        "/api/v1/projects",
        json={"name": "Strictness", "location": "Dadu", "unexpected": "x"},
    )
    assert r.status_code == 422


def test_unknown_update_field_is_rejected():
    created = client.post(
        "/api/v1/projects",
        json={"name": "Strictness", "location": "Dadu"},
    )
    pid = created.json()["id"]
    r = client.patch(
        f"/api/v1/projects/{pid}",
        json={"unexpected": "x"},
    )
    assert r.status_code == 422
