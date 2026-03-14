"""Fighter Rating Engine.

Computes a composite 0–10 rating from per-fighter features.

Rating components (each normalized to [0, 1] before combining):
    activity         25%  — exponential decay by days since last fight
    form             25%  — win streak + recent win rate
    efficiency       20%  — striking output + grappling volume
    opponent_quality 15%  — strength-of-schedule proxy
    finish_ability   15%  — finish rate

Output: FighterRating dataclass with per-component scores and a composite rating.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_ACTIVITY_HALF_LIFE_DAYS = 365.0

_WEIGHTS = {
    "activity": 0.25,
    "form": 0.25,
    "efficiency": 0.20,
    "opponent_quality": 0.15,
    "finish_ability": 0.15,
}


@dataclass(frozen=True)
class FighterRating:
    fighter_id: str
    name: str
    division: str
    activity_score: float        # 0–1
    form_score: float            # 0–1
    efficiency_score: float      # 0–1
    opponent_quality_score: float  # 0–1
    finish_ability_score: float  # 0–1
    rating: float                # 0–10 composite


def _f(row: dict, key: str, default: float = 0.0) -> float:
    """Safe float extraction from a features dict row."""
    val = row.get(key, default)
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _activity_score(recency_days: float) -> float:
    """Exponential decay: recent fight = high score, stale = low score."""
    return max(0.0, min(1.0, math.pow(2.0, -max(recency_days, 0.0) / _ACTIVITY_HALF_LIFE_DAYS)))


def _form_score(win_streak: float, last_5_win_pct: float) -> float:
    """Combined form from streak (40%) and recent win rate (60%)."""
    streak_component = min(win_streak / 5.0, 1.0)   # 5-fight streak = 1.0
    pct_component = max(0.0, min(1.0, last_5_win_pct))
    return 0.4 * streak_component + 0.6 * pct_component


def _efficiency_score(sig_str_per_min: float, td_rate: float, control_per_15: float) -> float:
    """Striking (50%) + grappling accuracy (30%) + control volume (20%)."""
    strike_norm = min(max(sig_str_per_min, 0.0) / 8.0, 1.0)   # cap at 8 sig/min
    td_norm = max(0.0, min(td_rate, 1.0))
    control_norm = min(max(control_per_15, 0.0) / 120.0, 1.0)  # cap at 120s/15min
    return 0.5 * strike_norm + 0.3 * td_norm + 0.2 * control_norm


def rate_fighter(row: dict) -> FighterRating:
    """Compute a FighterRating from a single features row dict."""
    activity = _activity_score(_f(row, "activity_recency_days", 999.0))
    form = _form_score(_f(row, "win_streak"), _f(row, "last_5_win_pct"))
    efficiency = _efficiency_score(
        _f(row, "sig_str_diff_per_min"),
        _f(row, "td_rate"),
        _f(row, "control_per_15"),
    )
    opp_quality = max(0.0, min(1.0, _f(row, "opponent_recent_win_pct_avg", 0.5)))
    finish = max(0.0, min(1.0, _f(row, "finish_rate")))

    composite = (
        _WEIGHTS["activity"] * activity
        + _WEIGHTS["form"] * form
        + _WEIGHTS["efficiency"] * efficiency
        + _WEIGHTS["opponent_quality"] * opp_quality
        + _WEIGHTS["finish_ability"] * finish
    )

    return FighterRating(
        fighter_id=row.get("fighter_id", ""),
        name=row.get("name", "Unknown"),
        division=row.get("weight_class", "Unknown"),
        activity_score=round(activity, 4),
        form_score=round(form, 4),
        efficiency_score=round(efficiency, 4),
        opponent_quality_score=round(opp_quality, 4),
        finish_ability_score=round(finish, 4),
        rating=round(composite * 10.0, 3),
    )


def rate_all(rows: list[dict]) -> list[FighterRating]:
    """Rate a list of fighters from features rows, returning in same order."""
    return [rate_fighter(r) for r in rows]
