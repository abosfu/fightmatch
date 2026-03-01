"""Disk cache with TTL for raw HTTP responses."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path


def cache_key(url: str) -> str:
    """Stable key from URL (safe filename)."""
    return hashlib.sha256(url.encode()).hexdigest()[:32]


class DiskCache:
    """TTL-based disk cache: cache_key(url) -> path, is_valid(ttl), read/write bytes."""

    def __init__(self, cache_dir: Path, ttl_seconds: int = 86400 * 7):
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.cache"

    def is_valid(self, key: str) -> bool:
        """True if cached entry exists and is within TTL."""
        p = self._path(key)
        if not p.exists():
            return False
        age = time.time() - p.stat().st_mtime
        return age <= self.ttl_seconds

    def read(self, key: str) -> bytes | None:
        """Return cached bytes or None if missing/expired."""
        if not self.is_valid(key):
            return None
        try:
            return self._path(key).read_bytes()
        except OSError:
            return None

    def write(self, key: str, data: bytes) -> None:
        """Write bytes to cache."""
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get_or_none(self, url: str) -> bytes | None:
        """Convenience: key from url, return cached body or None."""
        return self.read(cache_key(url))

    def set(self, url: str, data: bytes) -> None:
        """Convenience: key from url, write body."""
        self.write(cache_key(url), data)
