"""Configuration and business knobs for matchmaking."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScrapeConfig:
    """Scraping behavior."""
    base_url: str = "https://www.ufcstats.com"
    rate_limit_seconds: float = 1.0
    rate_limit_jitter: float = 0.3
    request_timeout: int = 30
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    user_agent: str = "FightMatch/0.1 (UFC decision-support; rate-limited)"


@dataclass
class CacheConfig:
    """Disk cache for raw responses."""
    dir: Path = field(default_factory=lambda: Path("data/raw/ufcstats"))
    ttl_seconds: int = 86400 * 7  # 7 days


@dataclass
class MatchConfig:
    """Business knobs for ranking and matchup scoring."""
    prioritize_contender_clarity: bool = True   # rank merit over name
    prioritize_action: bool = False            # favor finish_rate + high pace
    allow_short_notice: bool = False            # relax activity_recency constraint
    decay_half_life_days: float = 365.0        # exponential decay for older fights
    avoid_immediate_rematch: bool = True       # skip recent same pairing


def get_cache_dir() -> Path:
    return Path(os.environ.get("FIGHTMATCH_CACHE_DIR", "data/raw/ufcstats"))


def get_processed_dir() -> Path:
    return Path(os.environ.get("FIGHTMATCH_PROCESSED_DIR", "data/processed"))


def get_features_dir() -> Path:
    return Path(os.environ.get("FIGHTMATCH_FEATURES_DIR", "data/features"))
