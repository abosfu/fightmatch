"""Fighter Consistency and Volatility Metrics.

Derives consistency and volatility labels from available per-fighter features.
These are aggregated proxies computed from the features CSV — not per-fight
time-series variance — and should be read as style/reliability archetypes.

consistency_score (0–1)
    Measures how reliably this fighter performs recently.
    Combines recent win rate, current win streak, and activity regularity.

volatility_label
    "Stable"                — high win rate, decision-oriented output
    "High-Risk / High-Reward" — high finish rate dominates outcomes
    "Inconsistent"          — low win rate without a clear finishing pattern
    "Steady"                — moderate win rate, balanced output
"""

from __future__ import annotations


def consistency_score(
    last_5_win_pct: float,
    win_streak: float,
    activity_recency_days: float,
) -> float:
    """
    Composite consistency score (0–1). Higher = more reliable recent performance.

    Components:
        50%  recent win rate
        30%  current win streak (capped at 3 fights)
        20%  activity regularity (linear decay to 0 at 730 days)
    """
    win_component = max(0.0, min(1.0, last_5_win_pct))
    streak_component = min(max(win_streak, 0.0) / 3.0, 1.0)
    activity_component = max(0.0, 1.0 - activity_recency_days / 730.0)
    score = 0.50 * win_component + 0.30 * streak_component + 0.20 * activity_component
    return round(score, 4)


def volatility_label(last_5_win_pct: float, finish_rate: float) -> str:
    """
    Rule-based volatility classification.

    Winning recently + low finish rate  →  Stable (consistent decision wins)
    High finish rate (≥ 0.65)           →  High-Risk / High-Reward
    Low win rate + low finish rate      →  Inconsistent
    Otherwise                           →  Steady
    """
    winning = last_5_win_pct >= 0.60
    elite_finisher = finish_rate >= 0.65

    if winning and not elite_finisher:
        return "Stable"
    if elite_finisher:
        return "High-Risk / High-Reward"
    if not winning:
        return "Inconsistent"
    return "Steady"
