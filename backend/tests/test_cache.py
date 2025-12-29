"""Cache helper tests. These must never raise even when Redis is unavailable."""
from __future__ import annotations

import app.core.cache as cache


def test_dashboard_cache_key():
    assert cache.dashboard_cache_key(7) == "analytics:dashboard:7"


def test_cache_roundtrip_or_graceful_noop():
    key = "test:cache:roundtrip"
    # Should not raise regardless of Redis availability.
    cache.cache_set(key, {"a": 1}, ttl_seconds=5)
    value = cache.cache_get(key)
    # When Redis is up we get the value back; when down we get None.
    assert value in ({"a": 1}, None)
    cache.cache_delete(key)


def test_cache_get_missing_key_returns_none():
    assert cache.cache_get("test:cache:does-not-exist-xyz") is None


def test_cache_delete_no_keys_is_safe():
    cache.cache_delete()  # no-op, must not raise
