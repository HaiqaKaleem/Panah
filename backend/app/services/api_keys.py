"""
API Key Management & Rate Limiting

Provides:
  - API key generation and validation
  - Per-key rate limiting (sliding window)
  - Usage tracking per key
  - Tier-based limits (free, pro, enterprise)

In production, replace with Redis-backed rate limiting.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any


# -------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------

@dataclass
class APIKey:
    """An API key with metadata."""
    key_id: str
    key_hash: str
    name: str
    tier: str  # "free", "pro", "enterprise"
    created_at: str
    expires_at: str | None = None
    is_active: bool = True
    allowed_endpoints: list[str] = field(default_factory=list)  # empty = all
    metadata: dict[str, Any] = field(default_factory=dict)

    # Usage tracking
    total_requests: int = 0
    last_used_at: str | None = None

    def to_dict(self, show_key: bool = False) -> dict[str, Any]:
        d = {
            "key_id": self.key_id,
            "name": self.name,
            "tier": self.tier,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
            "total_requests": self.total_requests,
            "last_used_at": self.last_used_at,
        }
        if show_key:
            d["key_preview"] = self.key_hash[:8] + "..."
        return d


TIER_LIMITS: dict[str, dict[str, int]] = {
    # tier: {requests_per_minute, requests_per_hour, requests_per_day}
    "free": {"rpm": 30, "rph": 500, "rpd": 5000},
    "pro": {"rpm": 120, "rph": 5000, "rpd": 50000},
    "enterprise": {"rpm": 600, "rph": 50000, "rpd": 500000},
}


# -------------------------------------------------------------------
# Storage (in-memory, would be Redis in production)
# -------------------------------------------------------------------

_api_keys: dict[str, APIKey] = {}  # key_id -> APIKey
_key_by_hash: dict[str, str] = {}  # hash -> key_id
_rate_windows: dict[str, list[float]] = defaultdict(list)  # key_id -> [timestamps]


# -------------------------------------------------------------------
# Key management
# -------------------------------------------------------------------

def generate_api_key(
    name: str,
    tier: str = "free",
    expires_in_days: int | None = None,
    allowed_endpoints: list[str] | None = None,
) -> tuple[str, APIKey]:
    """
    Generate a new API key.

    Returns:
        (raw_key, APIKey object)
    """
    raw_key = f"pk_{uuid.uuid4().hex}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_id = f"key_{uuid.uuid4().hex[:12]}"

    expires_at = None
    if expires_in_days:
        from datetime import timedelta
        expires = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        expires_at = expires.isoformat()

    api_key = APIKey(
        key_id=key_id,
        key_hash=key_hash,
        name=name,
        tier=tier,
        created_at=datetime.now(timezone.utc).isoformat(),
        expires_at=expires_at,
        allowed_endpoints=allowed_endpoints or [],
    )

    _api_keys[key_id] = api_key
    _key_by_hash[key_hash] = key_id

    return raw_key, api_key


def validate_api_key(raw_key: str) -> APIKey | None:
    """Validate an API key and return it if valid."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_id = _key_by_hash.get(key_hash)
    if key_id is None:
        return None

    api_key = _api_keys.get(key_id)
    if api_key is None or not api_key.is_active:
        return None

    # Check expiration
    if api_key.expires_at:
        try:
            expires = datetime.fromisoformat(api_key.expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expires:
                api_key.is_active = False
                return None
        except (ValueError, TypeError):
            pass

    return api_key


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key."""
    api_key = _api_keys.get(key_id)
    if api_key is None:
        return False
    api_key.is_active = False
    return True


def list_api_keys(tier: str | None = None) -> list[dict[str, Any]]:
    """List all API keys (without exposing full keys)."""
    keys = list(_api_keys.values())
    if tier:
        keys = [k for k in keys if k.tier == tier]
    return [k.to_dict() for k in keys]


def get_api_key_usage(key_id: str) -> dict[str, Any] | None:
    """Get usage stats for a specific API key."""
    api_key = _api_keys.get(key_id)
    if api_key is None:
        return None

    now = time.time()
    timestamps = _rate_windows.get(key_id, [])

    # Count requests in different windows
    rpm = sum(1 for t in timestamps if now - t < 60)
    rph = sum(1 for t in timestamps if now - t < 3600)
    rpd = sum(1 for t in timestamps if now - t < 86400)

    limits = TIER_LIMITS.get(api_key.tier, TIER_LIMITS["free"])

    return {
        "key_id": key_id,
        "tier": api_key.tier,
        "current_usage": {
            "requests_last_minute": rpm,
            "requests_last_hour": rph,
            "requests_last_day": rpd,
        },
        "limits": limits,
        "utilization": {
            "rpm_pct": round(rpm / limits["rpm"] * 100, 1),
            "rph_pct": round(rph / limits["rph"] * 100, 1),
            "rpd_pct": round(rpd / limits["rpd"] * 100, 1),
        },
        "total_requests": api_key.total_requests,
    }


# -------------------------------------------------------------------
# Rate limiting
# -------------------------------------------------------------------

def check_rate_limit(key_id: str) -> tuple[bool, dict[str, Any]]:
    """
    Check if a request is within rate limits.

    Returns:
        (is_allowed, rate_limit_info)
    """
    api_key = _api_keys.get(key_id)
    if api_key is None:
        return False, {"error": "Invalid API key"}

    limits = TIER_LIMITS.get(api_key.tier, TIER_LIMITS["free"])
    now = time.time()

    # Clean old timestamps (older than 24h)
    timestamps = _rate_windows[key_id]
    _rate_windows[key_id] = [t for t in timestamps if now - t < 86400]
    timestamps = _rate_windows[key_id]

    # Count in each window
    rpm = sum(1 for t in timestamps if now - t < 60)
    rph = sum(1 for t in timestamps if now - t < 3600)
    rpd = sum(1 for t in timestamps if now - t < 86400)

    info = {
        "tier": api_key.tier,
        "limit_rpm": limits["rpm"],
        "limit_rph": limits["rph"],
        "limit_rpd": limits["rpd"],
        "used_rpm": rpm,
        "used_rph": rph,
        "used_rpd": rpd,
        "remaining_rpm": max(0, limits["rpm"] - rpm),
        "remaining_rph": max(0, limits["rph"] - rph),
        "remaining_rpd": max(0, limits["rpd"] - rpd),
        "reset_rpm": int(60 - (now - (timestamps[-1] if timestamps else now))),
        "reset_rph": int(3600 - (now - (timestamps[0] if timestamps else now))),
    }

    # Check limits
    if rpm >= limits["rpm"]:
        return False, {**info, "error": "Rate limit exceeded (per minute)"}
    if rph >= limits["rph"]:
        return False, {**info, "error": "Rate limit exceeded (per hour)"}
    if rpd >= limits["rpd"]:
        return False, {**info, "error": "Rate limit exceeded (per day)"}

    # Record this request
    _rate_windows[key_id].append(now)
    api_key.total_requests += 1
    api_key.last_used_at = datetime.now(timezone.utc).isoformat()

    return True, info


def get_global_rate_stats() -> dict[str, Any]:
    """Get global rate limiting statistics."""
    total_keys = len(_api_keys)
    active_keys = sum(1 for k in _api_keys.values() if k.is_active)
    tier_counts = defaultdict(int)
    for k in _api_keys.values():
        tier_counts[k.tier] += 1

    return {
        "total_keys": total_keys,
        "active_keys": active_keys,
        "keys_by_tier": dict(tier_counts),
        "tier_limits": TIER_LIMITS,
    }
