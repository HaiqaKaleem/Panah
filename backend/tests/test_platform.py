"""
Tests for platform services:
  - Job queue
  - Webhooks
  - API keys & rate limiting
  - Caching layer
  - Geo-climate lookup
  - Model export (glTF, IFC, OBJ)
"""
import pytest

# ── Job Queue Tests ──

from app.services.job_queue import (
    create_job, get_job, list_jobs, cancel_job, retry_job,
    get_queue_stats, clear_completed, JobType,
)


class TestJobQueue:
    def test_create_job(self):
        job = create_job("design_generation", {"constraint_set_id": 1})
        assert job.job_id.startswith("job_")
        assert job.status == "pending"
        assert job.job_type == "design_generation"

    def test_get_job(self):
        job = create_job("validation", {"design_id": 5})
        fetched = get_job(job.job_id)
        assert fetched is not None
        assert fetched.job_id == job.job_id

    def test_list_jobs(self):
        create_job("design_generation", {})
        create_job("validation", {})
        jobs = list_jobs()
        assert len(jobs) >= 2

    def test_cancel_job(self):
        job = create_job("design_generation", {})
        cancelled = cancel_job(job.job_id)
        assert cancelled is not None
        assert cancelled.status == "cancelled"

    def test_retry_job(self):
        job = create_job("design_generation", {})
        from app.services.job_queue import update_job_status
        update_job_status(job.job_id, "failed", error="test error")
        retried = retry_job(job.job_id)
        assert retried is not None
        assert retried.retry_count == 1

    def test_queue_stats(self):
        stats = get_queue_stats()
        assert "total_jobs" in stats
        assert "by_status" in stats

    def test_serialization(self):
        job = create_job("report_generation", {"project_id": 1})
        d = job.to_dict()
        assert "job_id" in d
        assert "status" in d
        assert "progress" in d


# ── Webhook Tests ──

from app.services.webhooks import (
    register_webhook, unregister_webhook, list_webhooks,
    publish_event, get_webhook_stats, get_delivery_history,
)


class TestWebhooks:
    def test_register_webhook(self):
        wh = register_webhook("https://example.com/hook", ["design.generated"])
        assert wh.webhook_id.startswith("wh_")
        assert wh.url == "https://example.com/hook"
        assert "design.generated" in wh.events

    def test_list_webhooks(self):
        register_webhook("https://a.com/hook", ["*"])
        whs = list_webhooks()
        assert len(whs) >= 1

    def test_unregister_webhook(self):
        wh = register_webhook("https://temp.com/hook", ["test.event"])
        assert unregister_webhook(wh.webhook_id)

    def test_publish_event(self):
        register_webhook("https://test.com/hook", ["design.generated"])
        deliveries = publish_event("design.generated", {"design_id": 1})
        assert len(deliveries) >= 1

    def test_webhook_stats(self):
        stats = get_webhook_stats()
        assert "total_webhooks" in stats
        assert "total_deliveries" in stats

    def test_serialization(self):
        wh = register_webhook("https://example.com/hook", ["test.event"])
        d = wh.to_dict()
        assert "webhook_id" in d
        assert "url" in d
        assert "events" in d


# ── API Key Tests ──

from app.services.api_keys import (
    generate_api_key, validate_api_key, revoke_api_key,
    list_api_keys, get_api_key_usage, check_rate_limit,
)


class TestAPIKeys:
    def test_generate_key(self):
        raw, key = generate_api_key("Test App", tier="free")
        assert raw.startswith("pk_")
        assert key.key_id.startswith("key_")

    def test_validate_key(self):
        raw, key = generate_api_key("Test App")
        validated = validate_api_key(raw)
        assert validated is not None
        assert validated.key_id == key.key_id

    def test_invalid_key(self):
        assert validate_api_key("pk_invalid_key") is None

    def test_revoke_key(self):
        raw, key = generate_api_key("Test App")
        assert revoke_api_key(key.key_id)
        assert validate_api_key(raw) is None

    def test_rate_limiting(self):
        raw, key = generate_api_key("Rate Test", tier="free")
        # First request should be allowed
        allowed, info = check_rate_limit(key.key_id)
        assert allowed

    def test_list_keys(self):
        generate_api_key("List Test")
        keys = list_api_keys()
        assert len(keys) >= 1

    def test_key_usage(self):
        raw, key = generate_api_key("Usage Test")
        usage = get_api_key_usage(key.key_id)
        assert usage is not None
        assert "current_usage" in usage

    def test_serialization(self):
        raw, key = generate_api_key("Ser Test")
        d = key.to_dict()
        assert "key_id" in d
        assert "tier" in d


# ── Cache Tests ──

from app.services.cache import Cache, cached


class TestCache:
    def test_basic_set_get(self):
        cache = Cache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        cache = Cache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        cache = Cache(default_ttl=0)
        cache.set("key1", "value1", ttl=0)
        import time; time.sleep(0.01)
        assert cache.get("key1") is None

    def test_cache_stats(self):
        cache = Cache()
        cache.set("a", 1)
        cache.get("a")
        cache.get("miss")
        stats = cache.stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1

    def test_clear(self):
        cache = Cache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None

    def test_namespace_clear(self):
        cache = Cache()
        cache.set("ns1:a", 1)
        cache.set("ns2:b", 2)
        cache.clear("ns1")
        assert cache.get("ns1:a") is None
        assert cache.get("ns2:b") == 2

    def test_decorator(self):
        call_count = 0

        @cached(ttl=60, namespace="test")
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_func(5)
        result2 = expensive_func(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once due to caching


# ── Geo-Climate Tests ──

from app.engineering.geo_climate import lookup_climate, list_climate_zones, get_material_recommendations


class TestGeoClimate:
    def test_lookup_by_region(self):
        zone = lookup_climate(region_name="tropical_monsoon")
        assert zone.zone_name == "Tropical Monsoon"

    def test_lookup_by_coordinates(self):
        zone = lookup_climate(latitude=25.0, longitude=70.0)
        assert zone.zone_name is not None

    def test_list_zones(self):
        zones = list_climate_zones()
        assert len(zones) >= 4

    def test_material_recommendations(self):
        recs = get_material_recommendations("semi_arid_south_asia")
        assert len(recs) > 0

    def test_serialization(self):
        zone = lookup_climate(region_name="arid_desert")
        d = zone.to_dict()
        assert "zone_name" in d
        assert "recommended_materials" in d
        assert "hazards" in d


# ── Model Export Tests ──

from app.engineering.model_export import export_gltf_scene, export_ifc_structure, export_obj_mesh


class TestModelExport:
    def _sample_design(self):
        return {
            "version": "DV-001",
            "members": [
                {"id": "m1", "type": "beam", "material_id": "treated_bamboo",
                 "length_m": 5.0, "diameter_m": 0.10,
                 "start": {"x_m": 0, "y_m": 0, "z_m": 0},
                 "end": {"x_m": 5.0, "y_m": 0, "z_m": 0}},
                {"id": "m2", "type": "column", "material_id": "treated_bamboo",
                 "length_m": 2.5, "diameter_m": 0.10,
                 "start": {"x_m": 0, "y_m": 0, "z_m": 0},
                 "end": {"x_m": 0, "y_m": 2.5, "z_m": 0}},
            ],
            "connections": [
                {"id": "c1", "a": "m1", "b": "m2", "type": "bolted"},
            ],
        }

    def test_gltf_export(self):
        design = self._sample_design()
        gltf = export_gltf_scene(design)
        assert "asset" in gltf
        assert "meshes" in gltf
        assert "materials" in gltf
        assert len(gltf["meshes"]) == 2

    def test_ifc_export(self):
        design = self._sample_design()
        ifc = export_ifc_structure(design, "Test Project")
        assert "header" in ifc
        assert "structural_members" in ifc
        assert len(ifc["structural_members"]) == 2

    def test_obj_export(self):
        design = self._sample_design()
        obj = export_obj_mesh(design)
        assert "o m1" in obj
        assert "o m2" in obj
        assert "v " in obj
