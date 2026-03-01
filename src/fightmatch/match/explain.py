"""Explain why a matchup was recommended (3-6 bullet reasons)."""

from __future__ import annotations

from typing import Optional


def explain_matchup(
    fighter_a: dict,
    fighter_b: dict,
    rank_a: float,
    rank_b: float,
    rank_positions: Optional[tuple[int, int]] = None,
) -> list[str]:
    """
    Return 3-6 bullet reasons for "why this matchup".
    rank_positions: (position_a, position_b) in division ranking (1-based) if available.
    """
    reasons: list[str] = []
    rank_diff = abs(rank_a - rank_b)
    if rank_positions:
        reasons.append(
            f"Both top-{max(rank_positions[0], rank_positions[1])} by rank score, within {rank_diff:.2f} points"
        )
    else:
        reasons.append(f"Rank scores within {rank_diff:.2f} points ({rank_a:.2f} vs {rank_b:.2f})")
    # Streak vs opponent quality
    streak_a = fighter_a.get("win_streak") or 0
    streak_b = fighter_b.get("win_streak") or 0
    if streak_a >= 2 or streak_b >= 2:
        reasons.append(
            f"Fighter A on {streak_a}-fight streak; Fighter B on {streak_b}-fight streak"
        )
    opp_a = fighter_a.get("opponent_recent_win_pct_avg")
    opp_b = fighter_b.get("opponent_recent_win_pct_avg")
    if opp_a is not None or opp_b is not None:
        a_str = f"{opp_a:.2f}" if opp_a is not None else "N/A"
        b_str = f"{opp_b:.2f}" if opp_b is not None else "N/A"
        reasons.append(f"Opponent quality proxy: A {a_str}, B {b_str} in last fights")
    # Style
    sig_a = fighter_a.get("sig_str_diff_per_min") or 0
    sig_b = fighter_b.get("sig_str_diff_per_min") or 0
    td_a = fighter_a.get("td_attempts_per_15") or 0
    td_b = fighter_b.get("td_attempts_per_15") or 0
    reasons.append(
        f"Striking/grappling mix: A {sig_a:.1f} sig/min, {td_a:.1f} TD att/15; B {sig_b:.1f} sig/min, {td_b:.1f} TD att/15"
    )
    # Activity
    rec_a = fighter_a.get("activity_recency_days")
    rec_b = fighter_b.get("activity_recency_days")
    if rec_a is not None and rec_b is not None:
        max_rec = max(rec_a, rec_b)
        if max_rec <= 180:
            reasons.append(f"Both active within last 180 days (good booking probability proxy)")
        else:
            reasons.append(f"Last fight recency: A {rec_a} days, B {rec_b} days")
    # Cap at 6
    return reasons[:6]
