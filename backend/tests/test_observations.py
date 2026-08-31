from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def setup_media():
    p = client.post("/api/v1/projects", json={"name":"Observation Project","location":"Dadu"}).json()["id"]
    s = client.post(f"/api/v1/projects/{p}/sites", json={"name":"Site A"}).json()["id"]
    c = client.post(f"/api/v1/projects/{p}/sites/{s}/captures", json={"captured_at":"2026-08-22T10:30:00Z"}).json()["id"]
    m = client.post(f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media", files={"file":("site.jpg",b"image","image/jpeg")}).json()["id"]
    return p,s,c,m

def url(p,s,c,m):
    return f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media/{m}/observations"

def test_create_observation():
    p,s,c,m=setup_media()
    r=client.post(url(p,s,c,m),json={"observation_type":"terrain","label":"standing_water","confidence":0.89})
    assert r.status_code==201 and r.json()["status"]=="unconfirmed"

def test_bbox_validation():
    p,s,c,m=setup_media()
    r=client.post(url(p,s,c,m),json={"observation_type":"object","label":"tree","confidence":.9,"bbox_x":.8,"bbox_y":.1,"bbox_width":.4,"bbox_height":.2})
    assert r.status_code==422

def test_bbox_requires_all():
    p,s,c,m=setup_media()
    r=client.post(url(p,s,c,m),json={"observation_type":"object","label":"tree","confidence":.9,"bbox_x":.2})
    assert r.status_code==422

def test_invalid_type_rejected():
    p,s,c,m=setup_media()
    r=client.post(url(p,s,c,m),json={"observation_type":"engineering_safety","label":"safe","confidence":.99})
    assert r.status_code==422

def test_confidence_range():
    p,s,c,m=setup_media()
    for value in [-.1,1.1]:
        r=client.post(url(p,s,c,m),json={"observation_type":"terrain","label":"muddy_ground","confidence":value})
        assert r.status_code==422

def test_extra_field_rejected():
    p,s,c,m=setup_media()
    r=client.post(url(p,s,c,m),json={"observation_type":"terrain","label":"muddy_ground","confidence":.8,"safe_for_building":True})
    assert r.status_code==422

def test_confirm_and_reject():
    p,s,c,m=setup_media()
    created=client.post(url(p,s,c,m),json={"observation_type":"object","label":"tree","confidence":.7}).json()
    oid=created["id"]
    assert client.patch(f"{url(p,s,c,m)}/{oid}/status",json={"status":"confirmed"}).json()["status"]=="confirmed"
    assert client.patch(f"{url(p,s,c,m)}/{oid}/status",json={"status":"rejected"}).json()["status"]=="rejected"

def test_wrong_media_isolated():
    p,s,c,m1=setup_media()
    m2=client.post(f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media",files={"file":("second.jpg",b"second","image/jpeg")}).json()["id"]
    oid=client.post(url(p,s,c,m1),json={"observation_type":"object","label":"tree","confidence":.9}).json()["id"]
    r=client.patch(f"{url(p,s,c,m2)}/{oid}/status",json={"status":"confirmed"})
    assert r.status_code==404
