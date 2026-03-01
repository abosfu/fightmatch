"""Rank score per division: weighted sum with decay."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from fightmatch.config import MatchConfig


def load_features_csv(path: Path) -> list[dict]:
    """Load features from features.csv."""
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            # Coerce numeric
            for key in (
                "activity_recency_days", "win_streak", "last_5_win_pct",
                "sig_str_diff_per_min", "td_rate", "td_attempts_per_15",
                "control_per_15", "finish_rate", "opponent_recent_win_pct_avg",
            ):
                if key in r and r[key] not in ("", None):
                    try:
                        r[key] = float(r[key])
                    except (ValueError, TypeError):
                        r[key] = None
                else:
                    r[key] = None
            rows.append(r)
    return rows


def rank_score(
    row: dict,
    config: MatchConfig,
    half_life_days: Optional[float] = None,
    reference_recency_days: Optional[float] = None,
) -> float:
    """
    Single fighter rank score: weighted sum of recent wins, opponent quality, activity, finishes.
    Decay by recency (exponential decay by days since fight implied via activity_recency_days).
    """
    half = half_life_days or config.decay_half_life_days
    recency = row.get("activity_recency_days")
    if recency is None:
        recency = 999
    decay = 2.0 ** (-recency / half)
    win_streak = (row.get("win_streak") or 0) or 0
    last_5 = row.get("last_5_win_pct")
    last_5_val = last_5 if last_5 is not None else 0.5
    opp_qual = row.get("opponent_recent_win_pct_avg")
    opp_qual_val = opp_qual if opp_qual is not None else 0.5
    finish_rate = row.get("finish_rate")
    finish_val = finish_rate if finish_rate is not None else 0.0
    activity_bonus = 1.0 if (reference_recency_days is None or recency <= reference_recency_days) else 0.5
    if config.allow_short_notice:
        activity_bonus = 1.0
    score = (
        decay * (
            2.0 * win_streak
            + 1.5 * last_5_val
            + 1.0 * opp_qual_val
            + (1.5 * finish_val if config.prioritize_action else 0.5 * finish_val)
        )
        * activity_bonus
    )
    return round(score, 6)


def _normalize_division(wc: Optional[str]) -> str:
    if not wc:
        return ""
    return wc.strip().lower()


def rank_by_division(
    features_path: Path,
    division: str,
    config: Optional[MatchConfig] = None,
    top_n: int = 15,
) -> list[tuple[dict, float]]:
    """
    Load features, filter by division (weight class), compute rank score, return top_n (fighter row, score).
    """
    config = config or MatchConfig()
    rows = load_features_csv(features_path)
    target = _normalize_division(division)
    if target:
        rows = [r for r in rows if _normalize_division(r.get("weight_class")) == target]
    scored = [(r, rank_score(r, config)) for r in rows]
    scored.sort(key=lambda x: -x[1])
    return scored[:top_n]
