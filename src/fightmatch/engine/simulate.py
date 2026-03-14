"""Matchup Simulation Engine.

Evaluates a proposed fight between two fighters and returns:
    win_probability      — logistic model on rating delta
    competitiveness      — how close to 50/50
    style_contrast       — divergence of style profiles
    rank_impact          — divisional significance by rank position
    recommendation_summary + key_factors
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from fightmatch.analytics.rating import rate_fighter


def _f(row: dict, key: str, default: float = 0.0) -> float:
    val = row.get(key, default)
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


@dataclass(frozen=True)
class MatchupSimulation:
    fighter_a: str
    fighter_b: str
    rating_a: float
    rating_b: float
    win_prob_a: float            # 0–1
    win_prob_b: float            # 0–1
    competitiveness: float       # 0–1 (1.0 = perfect 50/50)
    competitiveness_label: str
    style_contrast: float        # 0–1
    style_contrast_label: str
    rank_impact: float           # 0–1
    rank_impact_label: str
    recommendation_summary: str
    key_factors: list[str]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _win_probability(rating_a: float, rating_b: float) -> tuple[float, float]:
    """Logistic win probability from 0–10 rating difference.
    A 1-point gap → ~62% probability for the higher-rated fighter.
    """
    prob_a = round(_sigmoid((rating_a - rating_b) * 0.5), 4)
    return prob_a, round(1.0 - prob_a, 4)


def _competitiveness(win_prob_a: float) -> float:
    """1.0 at 50/50; 0.0 at perfect 100/0."""
    return round(1.0 - abs(win_prob_a - 0.5) * 2.0, 4)


def _competitiveness_label(score: float) -> str:
    if score >= 0.85:
        return "Pick 'em"
    if score >= 0.70:
        return "Competitive"
    if score >= 0.50:
        return "Slight Edge"
    if score >= 0.30:
        return "Clear Favorite"
    return "Heavy Favorite"


def _style_contrast(row_a: dict, row_b: dict) -> float:
    """Divergence of style profiles across four dimensions."""
    sig_a = _f(row_a, "sig_str_diff_per_min")
    sig_b = _f(row_b, "sig_str_diff_per_min")
    td_a = _f(row_a, "td_attempts_per_15")
    td_b = _f(row_b, "td_attempts_per_15")
    ctrl_a = _f(row_a, "control_per_15")
    ctrl_b = _f(row_b, "control_per_15")
    fin_a = _f(row_a, "finish_rate")
    fin_b = _f(row_b, "finish_rate")

    sig_diff = abs(sig_a - sig_b) / 8.0
    td_diff = abs(td_a - td_b) / 8.0
    ctrl_diff = abs(ctrl_a - ctrl_b) / 120.0
    fin_diff = abs(fin_a - fin_b)

    contrast = (
        0.30 * min(sig_diff, 1.0)
        + 0.30 * min(td_diff, 1.0)
        + 0.20 * min(ctrl_diff, 1.0)
        + 0.20 * fin_diff
    )
    return round(min(contrast, 1.0), 4)


def _style_contrast_label(score: float) -> str:
    if score >= 0.55:
        return "Strong Style Clash"
    if score >= 0.35:
        return "Contrasting Styles"
    if score >= 0.18:
        return "Moderate Style Overlap"
    return "Similar Profiles"


def _rank_impact(
    rank_pos_a: Optional[int],
    rank_pos_b: Optional[int],
    n_fighters: int,
) -> float:
    """Higher-ranked fighters = higher divisional impact. Returns 0.5 if unknown."""
    if rank_pos_a is None or rank_pos_b is None or n_fighters <= 1:
        return 0.5
    avg_pos = (rank_pos_a + rank_pos_b) / 2.0
    impact = max(0.0, 1.0 - (avg_pos - 1.0) / max(n_fighters - 1.0, 1.0))
    return round(impact, 4)


def _rank_impact_label(score: float) -> str:
    if score >= 0.80:
        return "Title Eliminator"
    if score >= 0.60:
        return "High-Stakes Divisional Fight"
    if score >= 0.40:
        return "Contender Fight"
    if score >= 0.20:
        return "Mid-Card Matchup"
    return "Developmental Bout"


def _key_factors(
    row_a: dict,
    row_b: dict,
    name_a: str,
    name_b: str,
    win_prob_a: float,
) -> list[str]:
    factors: list[str] = []

    streak_a = int(_f(row_a, "win_streak"))
    streak_b = int(_f(row_b, "win_streak"))
    if streak_a >= 2:
        factors.append(f"{name_a} riding a {streak_a}-fight win streak")
    if streak_b >= 2:
        factors.append(f"{name_b} riding a {streak_b}-fight win streak")

    sig_a = _f(row_a, "sig_str_diff_per_min")
    sig_b = _f(row_b, "sig_str_diff_per_min")
    td_a = _f(row_a, "td_rate")
    td_b = _f(row_b, "td_rate")

    if sig_a >= 4.5 and td_b >= 0.5:
        factors.append(
            f"Classic striker-vs-grappler matchup: {name_a}'s output vs {name_b}'s wrestling"
        )
    elif td_a >= 0.5 and sig_b >= 4.5:
        factors.append(
            f"Classic striker-vs-grappler matchup: {name_b}'s output vs {name_a}'s wrestling"
        )
    elif abs(sig_a - sig_b) < 1.0 and abs(td_a - td_b) < 0.15:
        factors.append("Near-identical style profiles — outcome likely decided by execution and ring generalship")

    fin_a = _f(row_a, "finish_rate")
    fin_b = _f(row_b, "finish_rate")
    if fin_a >= 0.65 and fin_b >= 0.65:
        factors.append("Both fighters carry elite finishing ability — stoppage expected")
    elif fin_a >= 0.65:
        factors.append(f"{name_a}'s finishing rate ({fin_a:.0%}) is a decisive threat")
    elif fin_b >= 0.65:
        factors.append(f"{name_b}'s finishing rate ({fin_b:.0%}) is a decisive threat")

    opp_a = _f(row_a, "opponent_recent_win_pct_avg", 0.5)
    opp_b = _f(row_b, "opponent_recent_win_pct_avg", 0.5)
    if opp_a >= 0.65 and opp_b >= 0.65:
        factors.append("Both fighters battle-tested against elite opposition")

    if abs(win_prob_a - 0.5) < 0.08:
        factors.append("Models project a genuine toss-up — hard to call on paper")
    elif win_prob_a >= 0.65:
        factors.append(f"{name_a} enters as a meaningful statistical favorite")
    elif win_prob_a <= 0.35:
        factors.append(f"{name_b} enters as a meaningful statistical favorite")

    return factors[:6]


def _recommendation_summary(
    competitiveness: float,
    style_contrast: float,
    rank_impact: float,
) -> str:
    tier_score = competitiveness * 0.40 + rank_impact * 0.40 + style_contrast * 0.20
    if tier_score >= 0.75:
        prefix = "PRIORITY MATCHUP"
    elif tier_score >= 0.55:
        prefix = "STRONG MATCHUP"
    elif tier_score >= 0.35:
        prefix = "VIABLE MATCHUP"
    else:
        prefix = "LOW PRIORITY"

    parts = []
    if rank_impact >= 0.70:
        parts.append("high divisional stakes")
    if competitiveness >= 0.80:
        parts.append("elite competitive balance")
    elif competitiveness >= 0.60:
        parts.append("solid competitive balance")
    if style_contrast >= 0.50:
        parts.append("strong style clash")
    detail = ", ".join(parts) if parts else "sufficient competitive merit"
    return f"{prefix} — {detail.capitalize()}"


def simulate(
    row_a: dict,
    row_b: dict,
    rank_pos_a: Optional[int] = None,
    rank_pos_b: Optional[int] = None,
    n_division_fighters: int = 0,
) -> MatchupSimulation:
    """Run a full matchup simulation between two feature rows."""
    rating_a = rate_fighter(row_a)
    rating_b = rate_fighter(row_b)

    win_prob_a, win_prob_b = _win_probability(rating_a.rating, rating_b.rating)
    comp = _competitiveness(win_prob_a)
    contrast = _style_contrast(row_a, row_b)
    impact = _rank_impact(rank_pos_a, rank_pos_b, n_division_fighters)

    name_a = row_a.get("name") or rating_a.fighter_id
    name_b = row_b.get("name") or rating_b.fighter_id

    factors = _key_factors(row_a, row_b, name_a, name_b, win_prob_a)
    summary = _recommendation_summary(comp, contrast, impact)

    return MatchupSimulation(
        fighter_a=name_a,
        fighter_b=name_b,
        rating_a=rating_a.rating,
        rating_b=rating_b.rating,
        win_prob_a=win_prob_a,
        win_prob_b=win_prob_b,
        competitiveness=comp,
        competitiveness_label=_competitiveness_label(comp),
        style_contrast=contrast,
        style_contrast_label=_style_contrast_label(contrast),
        rank_impact=impact,
        rank_impact_label=_rank_impact_label(impact),
        recommendation_summary=summary,
        key_factors=factors,
    )


def simulation_to_dict(sim: MatchupSimulation) -> dict:
    """Serialize a MatchupSimulation to a JSON-safe dict."""
    return {
        "fighter_a": sim.fighter_a,
        "fighter_b": sim.fighter_b,
        "rating_a": sim.rating_a,
        "rating_b": sim.rating_b,
        "win_probability": {
            "fighter_a": sim.win_prob_a,
            "fighter_b": sim.win_prob_b,
        },
        "competitiveness": sim.competitiveness,
        "competitiveness_label": sim.competitiveness_label,
        "style_contrast": sim.style_contrast,
        "style_contrast_label": sim.style_contrast_label,
        "rank_impact": sim.rank_impact,
        "rank_impact_label": sim.rank_impact_label,
        "recommendation_summary": sim.recommendation_summary,
        "key_factors": sim.key_factors,
    }


def format_simulation_terminal(sim: MatchupSimulation) -> str:
    """Render a MatchupSimulation as a formatted terminal string."""
    bar_width = 20

    def _prob_bar(p: float) -> str:
        filled = round(p * bar_width)
        return "█" * filled + "░" * (bar_width - filled)

    lines = [
        f"",
        f"  {'=' * 52}",
        f"  Matchup Simulation",
        f"  {'=' * 52}",
        f"  {sim.fighter_a}  vs  {sim.fighter_b}",
        f"",
        f"  Ratings:       {sim.rating_a:.1f}  vs  {sim.rating_b:.1f}",
        f"  Win Prob:      [{_prob_bar(sim.win_prob_a)}] {sim.win_prob_a:.0%}",
        f"                 [{_prob_bar(sim.win_prob_b)}] {sim.win_prob_b:.0%}",
        f"",
        f"  Competitiveness:  {sim.competitiveness:.2f} / 1.0  ({sim.competitiveness_label})",
        f"  Style Contrast:   {sim.style_contrast:.2f} / 1.0  ({sim.style_contrast_label})",
        f"  Rank Impact:      {sim.rank_impact:.2f} / 1.0  ({sim.rank_impact_label})",
        f"",
        f"  Key Factors:",
    ]
    for factor in sim.key_factors:
        lines.append(f"    • {factor}")
    lines += [
        f"",
        f"  {sim.recommendation_summary}",
        f"",
    ]
    return "\n".join(lines)


def format_simulation_markdown(sim: MatchupSimulation) -> str:
    """Render a MatchupSimulation as a Markdown report string."""
    from datetime import datetime
    ts = datetime.now().isoformat(timespec="seconds")
    lines = [
        f"# Matchup Simulation: {sim.fighter_a} vs {sim.fighter_b}",
        f"",
        f"**Generated:** {ts}",
        f"",
        f"## Ratings & Win Probability",
        f"",
        f"| Fighter | Rating | Win Probability |",
        f"|---------|--------|-----------------|",
        f"| {sim.fighter_a} | {sim.rating_a:.1f} / 10 | {sim.win_prob_a:.0%} |",
        f"| {sim.fighter_b} | {sim.rating_b:.1f} / 10 | {sim.win_prob_b:.0%} |",
        f"",
        f"## Matchup Metrics",
        f"",
        f"| Metric | Score | Label |",
        f"|--------|-------|-------|",
        f"| Competitiveness | {sim.competitiveness:.2f} | {sim.competitiveness_label} |",
        f"| Style Contrast | {sim.style_contrast:.2f} | {sim.style_contrast_label} |",
        f"| Rank Impact | {sim.rank_impact:.2f} | {sim.rank_impact_label} |",
        f"",
        f"## Key Factors",
        f"",
    ]
    for factor in sim.key_factors:
        lines.append(f"- {factor}")
    lines += [
        f"",
        f"## Recommendation",
        f"",
        f"**{sim.recommendation_summary}**",
        f"",
    ]
    return "\n".join(lines)
