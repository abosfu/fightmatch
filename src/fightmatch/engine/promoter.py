"""Promoter Decision Scoring.

Scores a proposed matchup from a promoter/analyst perspective.
Used to rank and select matchup recommendations.

Components (each 0–1 before weighting):
    competitiveness      30%  — competitive balance from simulation
    divisional_relevance 20%  — rank position in division
    activity_readiness   20%  — both fighters recently active
    freshness            15%  — rematch avoidance
    style_interest       10%  — style contrast bonus
    fan_interest          5%  — finish rate proxy (fan engagement placeholder)

Recommendation tiers: Priority (≥0.75) | Strong (≥0.60) | Consider (≥0.45) | Pass
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fightmatch.engine.simulate import MatchupSimulation, simulate


def _f(row: dict, key: str, default: float = 0.0) -> float:
    val = row.get(key, default)
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


_WEIGHTS = {
    "competitiveness": 0.30,
    "divisional_relevance": 0.20,
    "activity_readiness": 0.20,
    "freshness": 0.15,
    "style_interest": 0.10,
    "fan_interest": 0.05,
}

_TIERS = [
    (0.75, "Priority"),
    (0.60, "Strong"),
    (0.45, "Consider"),
    (0.0, "Pass"),
]


@dataclass(frozen=True)
class PromoterScore:
    matchup: str
    competitiveness: float
    divisional_relevance: float
    activity_readiness: float
    freshness: float
    style_interest: float
    fan_interest: float
    total: float  # weighted composite 0–1
    tier: str  # Priority | Strong | Consider | Pass


def _activity_readiness(
    row_a: dict, row_b: dict, allow_short_notice: bool = False
) -> float:
    """Both fighters recently active? 1.0 = both active within 180 days."""
    if allow_short_notice:
        return 1.0

    def _score(days: float) -> float:
        if days <= 180:
            return 1.0
        if days >= 730:
            return 0.0
        return 1.0 - (days - 180.0) / 550.0

    days_a = _f(row_a, "activity_recency_days", 999.0)
    days_b = _f(row_b, "activity_recency_days", 999.0)
    return round((_score(days_a) + _score(days_b)) / 2.0, 4)


def _fan_interest(row_a: dict, row_b: dict) -> float:
    """Average finish rate as a fan engagement proxy."""
    fa = _f(row_a, "finish_rate")
    fb = _f(row_b, "finish_rate")
    return round((fa + fb) / 2.0, 4)


def score_matchup(
    sim: MatchupSimulation,
    row_a: dict,
    row_b: dict,
    is_recent_rematch: bool = False,
    allow_short_notice: bool = False,
) -> PromoterScore:
    """Compute a promoter decision score for a proposed matchup."""
    competitiveness = sim.competitiveness
    divisional_relevance = sim.rank_impact
    activity = _activity_readiness(row_a, row_b, allow_short_notice)
    freshness = 0.0 if is_recent_rematch else 1.0
    style_interest = sim.style_contrast
    fan_interest = _fan_interest(row_a, row_b)

    total = round(
        _WEIGHTS["competitiveness"] * competitiveness
        + _WEIGHTS["divisional_relevance"] * divisional_relevance
        + _WEIGHTS["activity_readiness"] * activity
        + _WEIGHTS["freshness"] * freshness
        + _WEIGHTS["style_interest"] * style_interest
        + _WEIGHTS["fan_interest"] * fan_interest,
        4,
    )
    tier = next(t for threshold, t in _TIERS if total >= threshold)

    return PromoterScore(
        matchup=f"{sim.fighter_a} vs {sim.fighter_b}",
        competitiveness=competitiveness,
        divisional_relevance=divisional_relevance,
        activity_readiness=activity,
        freshness=freshness,
        style_interest=style_interest,
        fan_interest=fan_interest,
        total=total,
        tier=tier,
    )


def select_matchups_ranked(
    rated_fighters: list[tuple[dict, float]],
    top_n: int,
    recent_pairs: Optional[set[tuple[str, str]]] = None,
    allow_short_notice: bool = False,
) -> list[tuple[dict, dict, MatchupSimulation, PromoterScore]]:
    """
    Select top_n non-overlapping matchups ordered by promoter score.

    rated_fighters: list of (features_row, rating) sorted by rating descending.
    Returns: list of (row_a, row_b, simulation, promoter_score).
    """
    recent_pairs = recent_pairs or set()
    n = len(rated_fighters)

    candidates: list[tuple[float, dict, dict, MatchupSimulation, PromoterScore]] = []

    for i, (row_a, _) in enumerate(rated_fighters):
        for j, (row_b, _) in enumerate(rated_fighters):
            if i >= j:
                continue
            id_a = row_a.get("fighter_id", "")
            id_b = row_b.get("fighter_id", "")
            pair = (min(id_a, id_b), max(id_a, id_b))
            is_rematch = pair in recent_pairs

            sim = simulate(
                row_a,
                row_b,
                rank_pos_a=i + 1,
                rank_pos_b=j + 1,
                n_division_fighters=n,
            )
            ps = score_matchup(
                sim,
                row_a,
                row_b,
                is_recent_rematch=is_rematch,
                allow_short_notice=allow_short_notice,
            )
            candidates.append((ps.total, row_a, row_b, sim, ps))

    candidates.sort(key=lambda x: -x[0])

    out: list[tuple[dict, dict, MatchupSimulation, PromoterScore]] = []
    booked: set[str] = set()  # prevent a fighter from appearing in multiple matchups

    for _, row_a, row_b, sim, ps in candidates:
        id_a = row_a.get("fighter_id", "")
        id_b = row_b.get("fighter_id", "")
        if id_a in booked or id_b in booked:
            continue
        booked.add(id_a)
        booked.add(id_b)
        out.append((row_a, row_b, sim, ps))
        if len(out) >= top_n:
            break

    return out
