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

    Heuristics:
    - Avoid immediate rematches (config.avoid_immediate_rematch)
    - Penalize large gaps in rank score and activity recency
    - Prefer active fighters
    - Prefer contender-clarity when both are highly ranked and close
    - Allow style-test matchups (striker vs grappler, or vs perceived vulnerabilities)
    - Optionally emphasize action (prioritize_action)
    """
    score = 0.0

    # Rank closeness / contender clarity
    rank_diff = abs(rank_a - rank_b)
    if config.prioritize_contender_clarity:
        score += max(0.0, 2.0 - rank_diff)
    else:
        score += max(0.0, 1.5 - rank_diff * 0.5)
    # Penalize very large rank gaps (e.g. squash matches)
    if rank_diff > 1.5:
        score -= 0.5 * (rank_diff - 1.5)

    # Activity and gaps
    rec_a = fighter_a.get("activity_recency_days")
    rec_b = fighter_b.get("activity_recency_days")
    if rec_a is not None and rec_b is not None:
        rec_a = rec_a or 999
        rec_b = rec_b or 999
        rec_diff = abs(rec_a - rec_b)
        # Similar activity: small gap is good
        if rec_diff < 180:
            score += 0.5
        # Penalize very large activity gaps
        if rec_diff > 365:
            score -= 0.5
        if rec_diff > 730:
            score -= 0.5
        # Prefer matchups where both are relatively active (last fight within ~1 year)
        if rec_a <= 365 and rec_b <= 365:
            score += 0.5
        # De-emphasize matchups where both are very inactive
        if rec_a > 730 and rec_b > 730:
            score -= 0.5

    # Avoid immediate rematch
    if config.avoid_immediate_rematch and recent_bout_pair:
        score -= 2.0

    # Style and vulnerabilities
    sig_a = fighter_a.get("sig_str_diff_per_min") or 0.0
    sig_b = fighter_b.get("sig_str_diff_per_min") or 0.0
    td_a = fighter_a.get("td_attempts_per_15") or 0.0
    td_b = fighter_b.get("td_attempts_per_15") or 0.0
    ctrl_a = fighter_a.get("control_per_15") or 0.0
    ctrl_b = fighter_b.get("control_per_15") or 0.0

    striker_a = sig_a > 4 and td_a < 2
    striker_b = sig_b > 4 and td_b < 2
    grappler_a = td_a > 2 or ctrl_a > 20
    grappler_b = td_b > 2 or ctrl_b > 20

    # Perceived vulnerabilities (very rough proxies)
    vuln_to_grappling_a = (fighter_a.get("td_rate") or 0) < 0.3 and ctrl_a < 10
    vuln_to_grappling_b = (fighter_b.get("td_rate") or 0) < 0.3 and ctrl_b < 10
    vuln_to_striking_a = sig_a < 0
    vuln_to_striking_b = sig_b < 0

    # Classic striker vs grappler contrast
    if (striker_a and grappler_b) or (grappler_a and striker_b):
        score += 0.8

    # Style-test scenarios: attack perceived vulnerabilities
    if grappler_a and vuln_to_grappling_b:
        score += 0.4
    if grappler_b and vuln_to_grappling_a:
        score += 0.4
    if striker_a and vuln_to_striking_b:
        score += 0.3
    if striker_b and vuln_to_striking_a:
        score += 0.3

    # Extra contender-clarity boost when both are clearly in the mix
    if config.prioritize_contender_clarity and min(rank_a, rank_b) >= 2.0 and rank_diff <= 0.75:
        score += 0.5

    # Action: finish rate + pace
    if config.prioritize_action:
        fa = fighter_a.get("finish_rate") or 0.0
        fb = fighter_b.get("finish_rate") or 0.0
        score += 0.3 * (fa + fb)

    return max(0.0, round(score, 4))


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
