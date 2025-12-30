"""Tiny Redis-backed cache helper for short-lived response caching.

All operations are best-effort: if Redis is unavailable the helpers degrade to
no-ops so the application keeps serving (just without caching).
"""
from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client = None
_init_failed = False


def _get_client():
    global _client, _init_failed
    if _client is not None or _init_failed:
        return _client
    try:
        import redis

        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        _client.ping()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis cache unavailable, caching disabled: %s", exc)
        _client = None
        _init_failed = True
    return _client


def cache_get(key: str) -> Any | None:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_get failed for %s: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 30) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_set failed for %s: %s", key, exc)


def cache_delete(*keys: str) -> None:
    client = _get_client()
    if client is None or not keys:
        return
    try:
        client.delete(*keys)
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_delete failed: %s", exc)


def dashboard_cache_key(user_id: int) -> str:
    return f"analytics:dashboard:{user_id}"
