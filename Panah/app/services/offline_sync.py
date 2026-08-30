"""Offline-first PWA service — sync queue, conflict resolution, and offline storage.

Designed for field workers with unreliable internet connectivity.
"""

import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/offline", tags=["Offline PWA"])


# ── Models ────────────────────────────────────────────────────────────

class SyncAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncItem(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: SyncAction
    data: dict
    client_timestamp: str
    status: SyncStatus = SyncStatus.PENDING
    server_timestamp: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


class SyncRequest(BaseModel):
    device_id: str
    items: list[SyncItem]
    last_sync_time: Optional[str] = None


class ConflictResolution(BaseModel):
    strategy: str = "server_wins"  # server_wins, client_wins, merge, manual
    merged_data: Optional[dict] = None


class OfflineConfig(BaseModel):
    service_worker_version: str = "1.0.0"
    cache_name: str = "panagah-v1"
    max_cache_size_mb: int = 50
    sync_interval_seconds: int = 30
    max_retries: int = 3
    background_sync: bool = True
    offline_pages: list[str] = [
        "/",
        "/dashboard",
        "/requirements",
        "/materials",
        "/generation",
        "/validation",
        "/review",
    ]


# ── Sync Queue ────────────────────────────────────────────────────────

class SyncQueue:
    """Offline sync queue with conflict detection and resolution."""

    def __init__(self):
        self._queue: list[SyncItem] = []
        self._completed: list[SyncItem] = []
        self._conflicts: list[dict] = []
        self._devices: dict[str, dict] = {}

    def add_item(self, item: SyncItem) -> SyncItem:
        """Add item to sync queue."""
        # Check for conflicts with existing pending items
        for existing in self._queue:
            if (existing.entity_type == item.entity_type and
                existing.entity_id == item.entity_id and
                existing.status == SyncStatus.PENDING):
                # Potential conflict — flag it
                item.status = SyncStatus.CONFLICT
                self._conflicts.append({
                    "existing": existing.model_dump(),
                    "incoming": item.model_dump(),
                    "detected_at": datetime.utcnow().isoformat(),
                })
                break

        self._queue.append(item)
        return item

    def process_queue(self, device_id: str) -> dict:
        """Process all pending items for a device."""
        self._devices[device_id] = {
            "last_sync": datetime.utcnow().isoformat(),
            "status": "syncing",
        }

        processed = 0
        failed = 0
        conflicts = 0

        for item in self._queue:
            if item.status == SyncStatus.PENDING:
                try:
                    # Simulate server processing
                    item.status = SyncStatus.COMPLETED
                    item.server_timestamp = datetime.utcnow().isoformat()
                    self._completed.append(item)
                    processed += 1
                except Exception as e:
                    item.status = SyncStatus.FAILED
                    item.error = str(e)
                    item.retry_count += 1
                    failed += 1
            elif item.status == SyncStatus.CONFLICT:
                conflicts += 1

        self._devices[device_id]["status"] = "synced"

        return {
            "device_id": device_id,
            "processed": processed,
            "failed": failed,
            "conflicts": conflicts,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def resolve_conflict(self, conflict_index: int,
                         resolution: ConflictResolution) -> dict:
        """Resolve a sync conflict."""
        if conflict_index >= len(self._conflicts):
            return {"error": "Invalid conflict index"}

        conflict = self._conflicts[conflict_index]

        if resolution.strategy == "server_wins":
            resolved = conflict["existing"]
        elif resolution.strategy == "client_wins":
            resolved = conflict["incoming"]
        elif resolution.strategy == "merge" and resolution.merged_data:
            resolved = resolution.merged_data
        else:
            resolved = conflict["existing"]  # Default to server

        # Remove resolved conflict
        self._conflicts.pop(conflict_index)

        return {
            "resolution": resolution.strategy,
            "resolved_data": resolved,
            "remaining_conflicts": len(self._conflicts),
        }

    def get_queue_status(self, device_id: Optional[str] = None) -> dict:
        """Get sync queue statistics."""
        pending = sum(1 for i in self._queue if i.status == SyncStatus.PENDING)
        completed = sum(1 for i in self._queue if i.status == SyncStatus.COMPLETED)
        failed = sum(1 for i in self._queue if i.status == SyncStatus.FAILED)

        return {
            "total_items": len(self._queue),
            "pending": pending,
            "completed": completed,
            "failed": failed,
            "conflicts": len(self._conflicts),
            "devices": self._devices,
        }

    def retry_failed(self) -> int:
        """Retry all failed items."""
        retried = 0
        for item in self._queue:
            if item.status == SyncStatus.FAILED and item.retry_count < 3:
                item.status = SyncStatus.PENDING
                item.error = None
                retried += 1
        return retried

    def clear_completed(self) -> int:
        """Clear completed items from queue."""
        count = sum(1 for i in self._queue if i.status == SyncStatus.COMPLETED)
        self._queue = [i for i in self._queue if i.status != SyncStatus.COMPLETED]
        return count


sync_queue = SyncQueue()


# ── PWA Config ────────────────────────────────────────────────────────

@router.get("/config", summary="PWA configuration")
async def pwa_config():
    """
    Get PWA configuration for service worker registration.

    Includes cache settings, offline pages, and sync configuration.
    """
    config = OfflineConfig()
    return {
        "service_worker": {
            "version": config.service_worker_version,
            "registration": "/sw.js",
            "scope": "/",
        },
        "cache": {
            "name": config.cache_name,
            "max_size_mb": config.max_cache_size_mb,
            "strategy": "stale-while-revalidate",
        },
        "sync": {
            "interval_seconds": config.sync_interval_seconds,
            "max_retries": config.max_retries,
            "background_sync": config.background_sync,
        },
        "offline_pages": config.offline_pages,
        "manifest": {
            "name": "PANAGAH — Shelter Design",
            "short_name": "PANAGAH",
            "description": "Humanitarian Shelter Assessment & Design Platform",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0C252A",
            "theme_color": "#2D6A4F",
            "icons": [
                {"src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            ],
        },
    }


# ── Sync Endpoints ────────────────────────────────────────────────────

@router.post("/sync", summary="Push offline changes to server")
async def push_sync(request: SyncRequest):
    """
    Push offline changes to the server.

    Accepts a batch of create/update/delete operations made offline.
    Detects conflicts and queues items for processing.
    """
    results = []
    for item in request.items:
        result = sync_queue.add_item(item)
        results.append({
            "id": result.id,
            "status": result.status,
            "entity": f"{result.entity_type}/{result.entity_id}",
        })

    return {
        "device_id": request.device_id,
        "items_received": len(request.items),
        "results": results,
        "conflicts": sum(1 for r in results if r["status"] == "conflict"),
    }


@router.post("/sync/process", summary="Process sync queue")
async def process_sync(device_id: str = Query(...)):
    """Process all pending sync items for a device."""
    return sync_queue.process_queue(device_id)


@router.get("/sync/status", summary="Get sync queue status")
async def sync_status(device_id: Optional[str] = Query(None)):
    """Get current sync queue statistics."""
    return sync_queue.get_queue_status(device_id)


@router.post("/sync/conflict/{conflict_index}/resolve", summary="Resolve conflict")
async def resolve_conflict(conflict_index: int, resolution: ConflictResolution):
    """Resolve a sync conflict with specified strategy."""
    return sync_queue.resolve_conflict(conflict_index, resolution)


@router.post("/sync/retry", summary="Retry failed sync items")
async def retry_sync():
    """Retry all failed sync items."""
    retried = sync_queue.retry_failed()
    return {"retried": retried, "status": "retrying"}


@router.post("/sync/clear", summary="Clear completed sync items")
async def clear_sync():
    """Clear completed items from the sync queue."""
    cleared = sync_queue.clear_completed()
    return {"cleared": cleared}


# ── Offline Data Endpoints ────────────────────────────────────────────

@router.get("/offline-data/{project_id}", summary="Get data for offline caching")
async def offline_data(project_id: str):
    """
    Get all data needed for offline operation.

    Returns project data, materials, designs, and rules that can be
    cached on the device for offline access.
    """
    return {
        "project_id": project_id,
        "cached_at": datetime.utcnow().isoformat(),
        "data": {
            "project": {"id": project_id, "name": "Project Data"},
            "materials": [],
            "designs": [],
            "rules": [],
            "templates": [],
        },
        "size_estimate_kb": 50,
        "valid_until": (datetime.utcnow().replace(
            hour=23, minute=59, second=59
        )).isoformat(),
    }


@router.get("/sw.js", include_in_schema=False)
async def service_worker():
    """Serve the service worker JavaScript file."""
    sw_code = """
const CACHE_NAME = 'panagah-v1';
const OFFLINE_URLS = [
    '/',
    '/dashboard',
    '/requirements',
    '/materials',
    '/generation',
    '/validation',
    '/review',
];

// Install — cache offline pages
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(OFFLINE_URLS))
    );
    self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Fetch — network first, fallback to cache
self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request)
            .then(response => {
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});

// Background Sync
self.addEventListener('sync', event => {
    if (event.tag === 'panagah-sync') {
        event.waitUntil(syncData());
    }
});

async function syncData() {
    // Process offline queue
    const clients = await self.clients.matchAll();
    clients.forEach(client => client.postMessage({type: 'sync-triggered'}));
}
"""
    from fastapi.responses import Response
    return Response(content=sw_code, media_type="application/javascript")
