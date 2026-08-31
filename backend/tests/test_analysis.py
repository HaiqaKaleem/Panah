from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def setup_media():
    p=client.post("/api/v1/projects",json={"name":"AI Project","location":"Dadu"}).json()["id"]
    s=client.post(f"/api/v1/projects/{p}/sites",json={"name":"Site A"}).json()["id"]
    c=client.post(f"/api/v1/projects/{p}/sites/{s}/captures",json={"captured_at":"2026-08-22T10:30:00Z"}).json()["id"]
    m=client.post(f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media",files={"file":("site.jpg",b"image","image/jpeg")}).json()["id"]
    return p,s,c,m

def test_analysis_creates_unconfirmed_observation():
    p,s,c,m=setup_media()
    r=client.post(f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media/{m}/analyze")
    assert r.status_code==201
    assert r.json()["observations_created"]==1
    assert r.json()["observations"][0]["status"]=="unconfirmed"

def test_analysis_never_returns_engineering_claim():
    p,s,c,m=setup_media()
    client.post(f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media/{m}/analyze")
    r=client.get(f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media/{m}/observations")
    labels=[x["label"] for x in r.json()]
    assert "safe" not in labels
    assert "structurally_safe" not in labels
    assert "load_capacity" not in labels

def test_missing_file_returns_404():
    p,s,c,m=setup_media()
    from app.storage.factory import get_media_storage
    storage=get_media_storage().root/"captures"/str(c)
    for item in storage.iterdir(): item.unlink()
    r=client.post(f"/api/v1/projects/{p}/sites/{s}/captures/{c}/media/{m}/analyze")
    assert r.status_code==404

def test_wrong_capture_rejected():
    p,s,c,m=setup_media()
    c2=client.post(f"/api/v1/projects/{p}/sites/{s}/captures",json={"captured_at":"2026-08-22T11:00:00Z"}).json()["id"]
    r=client.post(f"/api/v1/projects/{p}/sites/{s}/captures/{c2}/media/{m}/analyze")
    assert r.status_code==404
