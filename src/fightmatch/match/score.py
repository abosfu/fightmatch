"""Matchup scoring: competitiveness, freshness, style contrast, business knobs."""

from __future__ import annotations

from typing import Optional

from fightmatch.config import MatchConfig


def matchup_score(
    fighter_a: dict,
    fighter_b: dict,
    rank_a: float,
    rank_b: float,
    config: MatchConfig,
    recent_bout_pair: bool = False,
) -> float:
    """
    Score how good a matchup A vs B is.
    - Competitiveness: closeness in rank score + similar recent activity
    - Freshness: penalize immediate rematch unless configured
    - Style contrast: striking vs grappling
    - Business: prioritize_contender_clarity (close ranks), prioritize_action (finish + pace)
    """
    score = 0.0
    rank_diff = abs(rank_a - rank_b)
    # Closeness: prefer similar rank (contender clarity or competitive)
    if config.prioritize_contender_clarity:
        score += max(0, 2.0 - rank_diff)
    else:
        score += max(0, 1.5 - rank_diff * 0.5)
    # Similar activity
    rec_a = fighter_a.get("activity_recency_days")
    rec_b = fighter_b.get("activity_recency_days")
    if rec_a is not None and rec_b is not None:
        rec_diff = abs((rec_a or 999) - (rec_b or 999))
        if rec_diff < 180:
            score += 0.5
    # Avoid immediate rematch
    if config.avoid_immediate_rematch and recent_bout_pair:
        score -= 2.0
    # Style contrast: striker vs wrestler
    sig_a = fighter_a.get("sig_str_diff_per_min") or 0
    sig_b = fighter_b.get("sig_str_diff_per_min") or 0
    td_a = fighter_a.get("td_attempts_per_15") or 0
    td_b = fighter_b.get("td_attempts_per_15") or 0
    striker_a = sig_a > 4 and (td_a or 0) < 2
    striker_b = sig_b > 4 and (td_b or 0) < 2
    grappler_a = (td_a or 0) > 2
    grappler_b = (td_b or 0) > 2
    if (striker_a and grappler_b) or (grappler_a and striker_b):
        score += 0.8
    # Action: finish rate + pace
    if config.prioritize_action:
        fa = fighter_a.get("finish_rate") or 0
        fb = fighter_b.get("finish_rate") or 0
        score += 0.3 * (fa + fb)
    return max(0, round(score, 4))


def select_matchups(
    ranked: list[tuple[dict, float]],
    top_n: int,
    config: MatchConfig,
    recent_pairs: Optional[set[tuple[str, str]]] = None,
) -> list[tuple[dict, dict, float, float]]:
    """
    From ranked list (fighter, rank_score), pick top_n matchups by matchup_score.
    Returns list of (fighter_a, fighter_b, rank_a, rank_b) sorted by matchup score desc.
    recent_pairs: set of (id1, id2) that fought recently (normalized order).
    """
    recent_pairs = recent_pairs or set()
    matchups: list[tuple[float, dict, dict, float, float]] = []
    for i, (fa, ra) in enumerate(ranked):
        for j, (fb, rb) in enumerate(ranked):
            if i >= j:
                continue
            id_a = fa.get("fighter_id", "")
            id_b = fb.get("fighter_id", "")
            pair = (min(id_a, id_b), max(id_a, id_b))
            recent = pair in recent_pairs
            sc = matchup_score(fa, fb, ra, rb, config, recent_bout_pair=recent)
            matchups.append((sc, fa, fb, ra, rb))
    matchups.sort(key=lambda x: -x[0])
    out: list[tuple[dict, dict, float, float]] = []
    seen: set[tuple[str, str]] = set()
    for sc, fa, fb, ra, rb in matchups:
        id_a = fa.get("fighter_id", "")
        id_b = fb.get("fighter_id", "")
        pair = (min(id_a, id_b), max(id_a, id_b))
        if pair in seen:
            continue
        seen.add(pair)
        out.append((fa, fb, ra, rb))
        if len(out) >= top_n:
            break
    return out
