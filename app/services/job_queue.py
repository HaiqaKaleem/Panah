"""
Background Job Queue — Async task management for long-running operations.

Simulates a production job queue (like Celery/Redis) using in-memory storage.
In production, this would be replaced by Celery + Redis/RabbitMQ.

Features:
  - Job creation, status tracking, progress updates
  - Job types: design_generation, validation, report_generation, optimization
  - Priority levels: low, normal, high, critical
  - Retry logic with configurable attempts
  - Result caching
"""
from __future__ import annotations

import uuid
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from dataclasses import dataclass, field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(str, Enum):
    DESIGN_GENERATION = "design_generation"
    VALIDATION = "validation"
    REPORT_GENERATION = "report_generation"
    OPTIMIZATION = "optimization"
    BATCH_VALIDATION = "batch_validation"
    COST_ESTIMATION = "cost_estimation"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


PRIORITY_WEIGHTS = {
    "low": 1,
    "normal": 2,
    "high": 3,
    "critical": 4,
}


@dataclass
class Job:
    """A background job."""
    job_id: str
    job_type: str
    status: str = "pending"
    priority: str = "normal"
    progress: float = 0.0  # 0-100
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    input_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "priority": self.priority,
            "progress": round(self.progress, 1),
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "input_data": self.input_data,
            "metadata": self.metadata,
        }


# In-memory job store (would be Redis in production)
_jobs: dict[str, Job] = {}


def create_job(
    job_type: str,
    input_data: dict[str, Any],
    priority: str = "normal",
    max_retries: int = 3,
    metadata: dict[str, Any] | None = None,
) -> Job:
    """Create a new background job."""
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = Job(
        job_id=job_id,
        job_type=job_type,
        priority=priority,
        input_data=input_data,
        max_retries=max_retries,
        metadata=metadata or {},
    )
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Job | None:
    """Get a job by ID."""
    return _jobs.get(job_id)


def list_jobs(
    status: str | None = None,
    job_type: str | None = None,
    limit: int = 50,
) -> list[Job]:
    """List jobs with optional filtering."""
    jobs = list(_jobs.values())
    if status:
        jobs = [j for j in jobs if j.status == status]
    if job_type:
        jobs = [j for j in jobs if j.job_type == job_type]
    # Sort by created_at descending
    jobs.sort(key=lambda j: j.created_at, reverse=True)
    return jobs[:limit]


def update_job_status(
    job_id: str,
    status: str,
    progress: float | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> Job | None:
    """Update a job's status and optional fields."""
    job = _jobs.get(job_id)
    if job is None:
        return None

    job.status = status
    if progress is not None:
        job.progress = progress
    if result is not None:
        job.result = result
    if error is not None:
        job.error = error

    now = datetime.now(timezone.utc).isoformat()
    if status == "running" and job.started_at is None:
        job.started_at = now
    elif status in ("completed", "failed", "cancelled"):
        job.completed_at = now

    return job


def cancel_job(job_id: str) -> Job | None:
    """Cancel a pending or running job."""
    job = _jobs.get(job_id)
    if job is None:
        return None
    if job.status in ("completed", "failed", "cancelled"):
        return job
    return update_job_status(job_id, "cancelled")


def retry_job(job_id: str) -> Job | None:
    """Retry a failed job."""
    job = _jobs.get(job_id)
    if job is None:
        return None
    if job.status != "failed":
        return job
    if job.retry_count >= job.max_retries:
        return job

    job.retry_count += 1
    job.status = "retrying"
    job.error = None
    job.progress = 0.0
    job.started_at = None
    job.completed_at = None
    return job


def get_queue_stats() -> dict[str, Any]:
    """Get job queue statistics."""
    all_jobs = list(_jobs.values())
    status_counts = {}
    type_counts = {}
    for j in all_jobs:
        status_counts[j.status] = status_counts.get(j.status, 0) + 1
        type_counts[j.job_type] = type_counts.get(j.job_type, 0) + 1

    return {
        "total_jobs": len(all_jobs),
        "by_status": status_counts,
        "by_type": type_counts,
        "avg_progress": round(
            sum(j.progress for j in all_jobs) / max(len(all_jobs), 1), 1
        ),
    }


def clear_completed(max_age_seconds: int = 3600) -> int:
    """Clear completed jobs older than max_age_seconds. Returns count removed."""
    now = time.time()
    to_remove = []
    for job_id, job in _jobs.items():
        if job.status in ("completed", "cancelled"):
            if job.completed_at:
                try:
                    completed_ts = datetime.fromisoformat(job.completed_at.replace("Z", "+00:00"))
                    age = now - completed_ts.timestamp()
                    if age > max_age_seconds:
                        to_remove.append(job_id)
                except (ValueError, TypeError):
                    pass
    for job_id in to_remove:
        del _jobs[job_id]
    return len(to_remove)
