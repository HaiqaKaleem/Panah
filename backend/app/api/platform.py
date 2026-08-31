"""
Platform Services API — Job queue, webhooks, API keys, geo-climate, export.

Endpoints:
  POST   /jobs               — Create a background job
  GET    /jobs               — List jobs
  GET    /jobs/{id}          — Get job status
  POST   /jobs/{id}/cancel   — Cancel a job
  POST   /jobs/{id}/retry    — Retry a failed job
  GET    /jobs/stats         — Queue statistics

  POST   /webhooks           — Register a webhook
  GET    /webhooks           — List webhooks
  DELETE /webhooks/{id}      — Remove a webhook
  POST   /webhooks/test      — Send test event
  GET    /webhooks/stats     — Webhook stats

  POST   /api-keys           — Generate API key
  GET    /api-keys           — List API keys
  GET    /api-keys/{id}/usage — Key usage stats
  POST   /api-keys/{id}/revoke — Revoke key

  GET    /geo-climate        — Lookup climate zone
  GET    /geo-climate/zones  — List all climate zones

  POST   /export/gltf        — Export design as glTF
  POST   /export/ifc         — Export design as IFC
  POST   /export/obj         — Export design as OBJ mesh

  GET    /cache/stats        — Cache statistics
  POST   /cache/clear        — Clear cache
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Any

from app.services.job_queue import (
    create_job, get_job, list_jobs, cancel_job, retry_job, get_queue_stats, clear_completed,
    JobType, JobPriority,
)
from app.services.webhooks import (
    register_webhook, unregister_webhook, list_webhooks, publish_event,
    get_delivery_history, get_webhook_stats, EVENT_TYPES,
)
from app.services.api_keys import (
    generate_api_key, validate_api_key, revoke_api_key,
    list_api_keys, get_api_key_usage, get_global_rate_stats, TIER_LIMITS,
)
from app.services.cache import get_cache
from app.engineering.geo_climate import lookup_climate, list_climate_zones, get_material_recommendations
from app.engineering.model_export import export_gltf_scene, export_ifc_structure, export_obj_mesh

router = APIRouter(prefix="/platform", tags=["Platform Services"])


# ── Request schemas ──

class CreateJobRequest(BaseModel):
    job_type: str
    input_data: dict[str, Any] = {}
    priority: str = "normal"
    max_retries: int = 3

class RegisterWebhookRequest(BaseModel):
    url: str
    events: list[str] = ["*"]

class TestWebhookRequest(BaseModel):
    event_type: str = "design.generated"
    payload: dict[str, Any] = {}

class CreateAPIKeyRequest(BaseModel):
    name: str
    tier: str = "free"
    expires_in_days: int | None = None

class GeoClimateRequest(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    region_name: str | None = None

class GLTFExportRequest(BaseModel):
    design: dict[str, Any]

class IFCExportRequest(BaseModel):
    design: dict[str, Any]
    project_name: str = "Panagah Shelter"
    site_name: str = "Project Site"

class OBJExportRequest(BaseModel):
    design: dict[str, Any]


# ── Job Queue Endpoints ──

@router.post("/jobs", status_code=201, summary="Create a background job")
def api_create_job(req: CreateJobRequest):
    job = create_job(
        job_type=req.job_type,
        input_data=req.input_data,
        priority=req.priority,
        max_retries=req.max_retries,
    )
    return job.to_dict()


@router.get("/jobs", summary="List jobs")
def api_list_jobs(
    status: str | None = None,
    job_type: str | None = None,
    limit: int = Query(default=50, le=200),
):
    jobs = list_jobs(status=status, job_type=job_type, limit=limit)
    return {"jobs": [j.to_dict() for j in jobs], "count": len(jobs)}


@router.get("/jobs/stats", summary="Queue statistics")
def api_queue_stats():
    return get_queue_stats()


@router.get("/jobs/{job_id}", summary="Get job status")
def api_get_job(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.post("/jobs/{job_id}/cancel", summary="Cancel a job")
def api_cancel_job(job_id: str):
    job = cancel_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.post("/jobs/{job_id}/retry", summary="Retry a failed job")
def api_retry_job(job_id: str):
    job = retry_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.post("/jobs/cleanup", summary="Clear completed jobs")
def api_cleanup_jobs(max_age_seconds: int = 3600):
    removed = clear_completed(max_age_seconds)
    return {"removed": removed}


# ── Webhook Endpoints ──

@router.post("/webhooks", status_code=201, summary="Register a webhook")
def api_register_webhook(req: RegisterWebhookRequest):
    wh = register_webhook(url=req.url, events=req.events)
    return wh.to_dict(show_secret=True)


@router.get("/webhooks", summary="List webhooks")
def api_list_webhooks(event_type: str | None = None):
    return list_webhooks(event_type=event_type)


@router.delete("/webhooks/{webhook_id}", summary="Remove a webhook")
def api_remove_webhook(webhook_id: str):
    if not unregister_webhook(webhook_id):
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"deleted": True}


@router.post("/webhooks/test", summary="Send test event to webhooks")
def api_test_webhook(req: TestWebhookRequest):
    deliveries = publish_event(req.event_type, req.payload)
    return {"deliveries": len(deliveries), "results": [d.to_dict() for d in deliveries]}


@router.get("/webhooks/stats", summary="Webhook statistics")
def api_webhook_stats():
    return get_webhook_stats()


@router.get("/webhooks/events", summary="List available event types")
def api_list_events():
    return {"events": EVENT_TYPES}


@router.get("/webhooks/deliveries", summary="Delivery history")
def api_delivery_history(
    webhook_id: str | None = None,
    event_type: str | None = None,
    limit: int = Query(default=50, le=200),
):
    return get_delivery_history(webhook_id=webhook_id, event_type=event_type, limit=limit)


# ── API Key Endpoints ──

@router.post("/api-keys", status_code=201, summary="Generate API key")
def api_create_key(req: CreateAPIKeyRequest):
    raw_key, api_key = generate_api_key(
        name=req.name,
        tier=req.tier,
        expires_in_days=req.expires_in_days,
    )
    result = api_key.to_dict()
    result["key"] = raw_key  # Only shown once!
    return result


@router.get("/api-keys", summary="List API keys")
def api_list_keys(tier: str | None = None):
    return list_api_keys(tier=tier)


@router.get("/api-keys/{key_id}/usage", summary="Key usage stats")
def api_key_usage(key_id: str):
    usage = get_api_key_usage(key_id)
    if usage is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return usage


@router.post("/api-keys/{key_id}/revoke", summary="Revoke API key")
def api_revoke_key(key_id: str):
    if not revoke_api_key(key_id):
        raise HTTPException(status_code=404, detail="Key not found")
    return {"revoked": True}


@router.get("/api-keys/stats/rate-limits", summary="Rate limit tiers")
def api_rate_limit_info():
    return {"tiers": TIER_LIMITS, **get_global_rate_stats()}


# ── Geo-Climate Endpoints ──

@router.post("/geo-climate", summary="Lookup climate zone")
def api_geo_climate(req: GeoClimateRequest):
    zone = lookup_climate(
        latitude=req.latitude,
        longitude=req.longitude,
        region_name=req.region_name,
    )
    return zone.to_dict()


@router.get("/geo-climate/zones", summary="List all climate zones")
def api_list_climate_zones():
    return list_climate_zones()


@router.get("/geo-climate/materials/{climate_zone}", summary="Recommended materials for climate")
def api_climate_materials(climate_zone: str):
    materials = get_material_recommendations(climate_zone)
    return {"climate_zone": climate_zone, "recommended_materials": materials}


# ── Export Endpoints ──

@router.post("/export/gltf", summary="Export design as glTF 2.0 scene")
def api_export_gltf(req: GLTFExportRequest):
    gltf = export_gltf_scene(req.design)
    return Response(
        content=json.dumps(gltf, indent=2),
        media_type="model/gltf+json",
        headers={"Content-Disposition": 'attachment; filename="design.gltf"'},
    )


@router.post("/export/ifc", summary="Export design as IFC structure")
def api_export_ifc(req: IFCExportRequest):
    ifc = export_ifc_structure(req.design, req.project_name, req.site_name)
    return Response(
        content=json.dumps(ifc, indent=2),
        media_type="application/x-step",
        headers={"Content-Disposition": 'attachment; filename="design.ifc"'},
    )


@router.post("/export/obj", summary="Export design as OBJ mesh")
def api_export_obj(req: OBJExportRequest):
    obj = export_obj_mesh(req.design)
    return Response(
        content=obj,
        media_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="design.obj"'},
    )


# ── Cache Endpoints ──

@router.get("/cache/stats", summary="Cache statistics")
def api_cache_stats():
    return get_cache().stats()


@router.post("/cache/clear", summary="Clear cache")
def api_clear_cache(namespace: str | None = None):
    count = get_cache().clear(namespace)
    return {"cleared": count}


@router.post("/cache/cleanup", summary="Remove expired entries")
def api_cache_cleanup():
    removed = get_cache().cleanup()
    return {"expired_removed": removed}
