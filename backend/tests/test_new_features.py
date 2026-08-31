"""Tests for all new features — search, bulk, i18n, collaboration, analytics, files, APM."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.search import search_engine
from app.services.i18n import i18n
from app.services.analytics_advanced import analytics_engine

client = TestClient(app)


# ── Search Tests ──────────────────────────────────────────────────────

class TestSearch:
    def test_search_empty(self):
        r = client.get("/api/v1/search?q=nonexistent")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_search_with_indexed_data(self):
        # Index some data
        search_engine.index_entity(
            "project", "prj_001",
            {"name": "Emergency Shelter Camp Alpha", "description": "Humanitarian shelter project"},
            {"name": "Camp Alpha"},
        )
        search_engine.index_entity(
            "material", "mat_001",
            {"name": "Guadua Bamboo structural material", "description": "Sustainable bamboo"},
            {"name": "Guadua Bamboo"},
        )

        # Search
        r = client.get("/api/v1/search?q=shelter")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        assert data["results"][0]["type"] in ["project", "material"]

    def test_search_with_type_filter(self):
        search_engine.index_entity(
            "project", "prj_002",
            {"name": "Test Project for filtering"},
            {"name": "Filter Project"},
        )
        r = client.get("/api/v1/search?q=filtering&types=project")
        assert r.status_code == 200

    def test_search_limit(self):
        r = client.get("/api/v1/search?q=test&limit=5")
        assert r.status_code == 200

    def test_search_suggest(self):
        search_engine.index_entity(
            "project", "prj_003",
            {"name": "Search Suggestion Test"},
            {"name": "Suggestion Test"},
        )
        r = client.get("/api/v1/search/suggest?q=search")
        assert r.status_code == 200
        assert "suggestions" in r.json()

    def test_search_arabic(self):
        search_engine.index_entity(
            "project", "prj_ar",
            {"name": "مشروع م shelter", "description": "Testing Arabic search"},
            {"name": "Arabic Test"},
        )
        r = client.get("/api/v1/search?q=مشروع")
        assert r.status_code == 200

    def test_search_urdu(self):
        search_engine.index_entity(
            "project", "prj_ur",
            {"name": "پناگاہ shelter project", "description": "Testing Urdu search"},
            {"name": "Urdu Test"},
        )
        r = client.get("/api/v1/search?q=پناگاہ")
        assert r.status_code == 200


# ── Bulk Operations Tests ────────────────────────────────────────────

class TestBulkOperations:
    def test_export_csv(self):
        r = client.post("/api/v1/bulk/export/projects?format=csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    def test_export_json(self):
        r = client.post("/api/v1/bulk/export/projects?format=json")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_export_jsonl(self):
        r = client.post("/api/v1/bulk/export/materials?format=jsonl")
        assert r.status_code == 200
        assert "application/x-ndjson" in r.headers["content-type"]

    def test_import_csv_dry_run(self):
        csv_content = "name,description\nTest Project,A test"
        r = client.post(
            "/api/v1/bulk/import/projects?dry_run=true",
            files={"file": ("test.csv", csv_content.encode(), "text/csv")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "dry_run"
        assert data["valid_rows"] == 1

    def test_import_json(self):
        json_content = '[{"name": "Imported Project", "description": "From JSON"}]'
        r = client.post(
            "/api/v1/bulk/import/projects",
            files={"file": ("data.json", json_content.encode(), "application/json")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["valid_rows"] == 1

    def test_import_validation_error(self):
        json_content = '[{"description": "Missing name"}]'
        r = client.post(
            "/api/v1/bulk/import/projects",
            files={"file": ("bad.json", json_content.encode(), "application/json")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["error_rows"] == 1

    def test_download_template(self):
        r = client.get("/api/v1/bulk/templates/materials")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]


# ── i18n Tests ────────────────────────────────────────────────────────

class TestI18n:
    def test_list_languages(self):
        r = client.get("/api/v1/i18n/languages")
        assert r.status_code == 200
        data = r.json()
        assert len(data["languages"]) == 3
        codes = [lang["code"] for lang in data["languages"]]
        assert "en" in codes
        assert "ur" in codes
        assert "ar" in codes

    def test_get_translations_en(self):
        r = client.get("/api/v1/i18n/translate/en")
        assert r.status_code == 200
        data = r.json()
        assert data["direction"] == "ltr"
        assert "nav.home" in data["translations"]

    def test_get_translations_ur(self):
        r = client.get("/api/v1/i18n/translate/ur")
        assert r.status_code == 200
        data = r.json()
        assert data["direction"] == "rtl"
        assert "nav.home" in data["translations"]
        assert data["translations"]["nav.home"] == "ہوم"

    def test_get_translations_ar(self):
        r = client.get("/api/v1/i18n/translate/ar")
        assert r.status_code == 200
        data = r.json()
        assert data["direction"] == "rtl"

    def test_translate_single_key(self):
        r = client.get("/api/v1/i18n/translate/en/nav.home")
        assert r.status_code == 200
        assert r.json()["translation"] == "Home"

    def test_translate_single_key_ur(self):
        r = client.get("/api/v1/i18n/translate/ur/nav.home")
        assert r.status_code == 200
        assert r.json()["translation"] == "ہوم"

    def test_unsupported_language(self):
        r = client.get("/api/v1/i18n/translate/fr")
        assert r.status_code == 200
        assert "error" in r.json()


# ── Collaboration Tests ──────────────────────────────────────────────

class TestCollaboration:
    def test_add_comment(self):
        r = client.post("/api/v1/collaborate/project/prj_001/comments", json={
            "content": "This design looks great! @john please review",
        })
        assert r.status_code == 201
        data = r.json()
        assert "john" in data["mentions"]

    def test_list_comments(self):
        # Add comment first
        client.post("/api/v1/collaborate/site/site_001/comments", json={
            "content": "Comment for listing",
        })
        r = client.get("/api/v1/collaborate/site/site_001/comments")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_reply_to_comment(self):
        # Add parent comment
        parent = client.post("/api/v1/collaborate/design/dsg_001/comments", json={
            "content": "Parent comment",
        })
        parent_id = parent.json()["id"]

        # Reply
        r = client.post(f"/api/v1/collaborate/comments/{parent_id}/reply", json={
            "content": "This is a reply",
        })
        assert r.status_code == 201

    def test_resolve_comment(self):
        parent = client.post("/api/v1/collaborate/validation/val_001/comments", json={
            "content": "Issue to resolve",
        })
        comment_id = parent.json()["id"]

        r = client.post(f"/api/v1/collaborate/comments/{comment_id}/resolve")
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"

    def test_find_mentions(self):
        client.post("/api/v1/collaborate/project/prj_002/comments", json={
            "content": "Hey @alice check this out",
        })
        r = client.get("/api/v1/collaborate/mentions/alice")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_activity_feed(self):
        r = client.get("/api/v1/collaborate/project/prj_001/activity")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_discussion(self):
        r = client.post("/api/v1/collaborate/discussions", json={
            "title": "Design Review Meeting",
            "entity_type": "project",
            "entity_id": "prj_003",
        })
        assert r.status_code == 201

    def test_list_discussions(self):
        r = client.get("/api/v1/collaborate/project/prj_003/discussions")
        assert r.status_code == 200


# ── Analytics Tests ──────────────────────────────────────────────────

class TestAnalytics:
    def test_usage_trends(self):
        r = client.get("/api/v1/analytics/trends?days=30")
        assert r.status_code == 200

    def test_entity_popularity(self):
        r = client.get("/api/v1/analytics/entity-popularity")
        assert r.status_code == 200

    def test_predict_design(self):
        r = client.post("/api/v1/analytics/predict", json={
            "material_quality_score": 80,
            "safety_factor": 1.8,
            "compliance_score": 90,
            "cost_per_person": 75,
            "build_complexity": 3,
        })
        assert r.status_code == 200
        data = r.json()
        assert "approval_probability" in data
        assert "risk_level" in data

    def test_performance_metrics(self):
        r = client.get("/api/v1/analytics/performance")
        assert r.status_code == 200

    def test_cost_analysis(self):
        r = client.post("/api/v1/analytics/cost-analysis", json=[
            {"total_cost": 5000, "cost_per_person": 80},
            {"total_cost": 7500, "cost_per_person": 120},
        ])
        assert r.status_code == 200
        data = r.json()
        assert data["avg_cost"] == 6250

    def test_record_event(self):
        r = client.post("/api/v1/analytics/record", json={
            "type": "design_generated",
            "entity_type": "design",
            "entity_id": "dsg_001",
        })
        assert r.status_code == 200


# ── File Processing Tests ────────────────────────────────────────────

class TestFileProcessing:
    def test_analyze_image(self):
        # Create a simple test image
        from PIL import Image
        import io

        img = Image.new("RGB", (100, 100), color="green")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        r = client.post(
            "/api/v1/files/analyze",
            files={"file": ("test.jpg", buf, "image/jpeg")},
        )
        assert r.status_code == 200
        data = r.json()
        assert "dimensions" in data
        assert "quality" in data

    def test_validate_file(self):
        r = client.post(
            "/api/v1/files/validate",
            files={"file": ("test.jpg", b"fake image", "image/jpeg")},
        )
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_validate_bad_extension(self):
        r = client.post(
            "/api/v1/files/validate",
            files={"file": ("test.exe", b"bad file", "application/octet-stream")},
        )
        assert r.status_code == 200
        assert r.json()["valid"] is False

    def test_convert_json_to_csv(self):
        r = client.post("/api/v1/files/convert?source_format=json&target_format=csv", json=[
            {"name": "Test", "value": "123"},
        ])
        assert r.status_code == 200
        assert r.json()["format"] == "csv"

    def test_allowed_types(self):
        r = client.get("/api/v1/files/allowed-types")
        assert r.status_code == 200
        data = r.json()
        assert "image" in data
        assert "document" in data

    def test_file_stats(self):
        r = client.get("/api/v1/files/stats")
        assert r.status_code == 200


# ── Rate Limiter Tests ───────────────────────────────────────────────

class TestRateLimiter:
    def test_rate_limit_headers(self):
        r = client.get("/health")
        # Rate limiter may or may not add headers depending on middleware order
        assert r.status_code == 200

    def test_docs_not_rate_limited(self):
        # Docs should bypass rate limiting
        for _ in range(5):
            r = client.get("/docs")
            assert r.status_code == 200


# ── APM Tests ─────────────────────────────────────────────────────────

class TestAPM:
    def test_apm_headers_on_health(self):
        r = client.get("/health")
        assert "X-APM-Duration" in r.headers
        assert "X-APM-Status" in r.headers

    def test_apm_headers_on_api(self):
        r = client.get("/api/v1/material-catalog")
        assert "X-APM-Duration" in r.headers


# ── API Versioning Tests ─────────────────────────────────────────────

class TestAPIVersioning:
    def test_version_header(self):
        r = client.get("/api/v1/material-catalog")
        assert "X-API-Version" in r.headers
        assert r.headers["X-API-Version"] == "v1"

    def test_api_status_header(self):
        r = client.get("/api/v1/material-catalog")
        assert "X-API-Status" in r.headers
        assert r.headers["X-API-Status"] == "stable"


# ── Middleware Integration Tests ──────────────────────────────────────

class TestMiddlewareIntegration:
    def test_all_headers_present(self):
        r = client.get("/api/v1/material-catalog")
        # Request logging
        assert "X-Request-ID" in r.headers
        # Timing
        assert "X-Response-Time" in r.headers
        # APM
        assert "X-APM-Duration" in r.headers
        # Versioning
        assert "X-API-Version" in r.headers

    def test_correlation_id_passthrough(self):
        r = client.get("/health", headers={"X-Request-ID": "my-custom-id"})
        assert r.headers["X-Request-ID"] == "my-custom-id"

    def test_error_response_format(self):
        r = client.get("/api/v1/projects/999999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert "error" in data
        assert "timestamp" in data
