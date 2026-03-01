"""Test DiskCache TTL behavior."""

import time
from pathlib import Path
import tempfile

import pytest

from fightmatch.cache import DiskCache, cache_key


def test_cache_key():
    assert cache_key("https://a.com/x") != cache_key("https://a.com/y")
    assert len(cache_key("https://a.com")) == 32


def test_cache_ttl():
    with tempfile.TemporaryDirectory() as d:
        cache = DiskCache(Path(d), ttl_seconds=1)
        k = "testkey"
        cache.write(k, b"hello")
        assert cache.is_valid(k) is True
        assert cache.read(k) == b"hello"
        time.sleep(1.1)
        assert cache.is_valid(k) is False
        assert cache.read(k) is None


def test_cache_get_set_by_url():
    with tempfile.TemporaryDirectory() as d:
        cache = DiskCache(Path(d), ttl_seconds=60)
        cache.set("https://example.com/page", b"body")
        assert cache.get_or_none("https://example.com/page") == b"body"
        assert cache.get_or_none("https://other.com") is None
