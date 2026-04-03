"""Fighter Analytics Profile builder.

Assembles a comprehensive, human-readable profile for a single fighter
from a features row. Computes division-relative percentile ranking,
style archetype, and all descriptive labels used in reports.
"""

from __future__ import annotations

from dataclasses import dataclass

from fightmatch.analytics.consistency import (
    consistency_score as _consistency_score,
    volatility_label as _volatility_label,
)
from fightmatch.analytics.rating import FighterRating, rate_fighter, rate_all, _f


@dataclass
class FighterProfile:
    # Identity
    fighter_id: str
    name: str
    division: str

    # Rating
    rating: FighterRating
    rating_percentile: float  # 0–100 within division (100 = top)

    # Activity
    days_since_last_fight: float
    activity_status: str  # "Active" | "Semi-Active" | "Inactive"

    # Form & momentum
    win_streak: int
    last_5_win_pct: float
    momentum: str  # "Rising" | "Steady" | "Declining"

    # Striking
    sig_str_per_min: float
    striking_label: str  # "High-Volume" | "Technical" | "Average" | "Limited"

    # Grappling
    td_rate: float
    td_per_15: float
    control_per_15: float
    grappling_label: (
        str  # "Dominant Grappler" | "Active Wrestler" | "Balanced" | "Striker"
    )

    # Finishing
    finish_rate: float
    finish_label: (
        str  # "Elite Finisher" | "High Finisher" | "Balanced" | "Decision Fighter"
    )

    # Strength of schedule
    opp_win_pct_avg: float
    sos_label: str  # "Elite" | "Strong" | "Moderate" | "Developing"

    # Style synthesis
    style_archetype: str

    # Reliability
    consistency_score: float  # 0–1 composite reliability metric
    volatility_label: (
        str  # "Stable" | "High-Risk / High-Reward" | "Inconsistent" | "Steady"
    )


# ── Label helpers ─────────────────────────────────────────────────────────────


def _activity_status(days: float) -> str:
    if days <= 180:
        return "Active"
    if days <= 365:
        return "Semi-Active"
    return "Inactive"


def _momentum(win_streak: int, last_5_win_pct: float, activity_days: float) -> str:
    if win_streak >= 2 and last_5_win_pct >= 0.6:
        return "Rising"
    if last_5_win_pct >= 0.5 and activity_days <= 365:
        return "Steady"
    return "Declining"


def _striking_label(sig_per_min: float) -> str:
    if sig_per_min >= 5.0:
        return "High-Volume"
    if sig_per_min >= 3.5:
        return "Technical"
    if sig_per_min >= 2.0:
        return "Average"
    return "Limited"


def _grappling_label(td_rate: float, td_per_15: float, control_per_15: float) -> str:
    if td_rate >= 0.55 and control_per_15 >= 60:
        return "Dominant Grappler"
    if td_per_15 >= 4.0 or td_rate >= 0.5:
        return "Active Wrestler"
    if td_per_15 >= 2.0 or control_per_15 >= 20:
        return "Balanced"
    return "Striker"


def _finish_label(finish_rate: float) -> str:
    if finish_rate >= 0.75:
        return "Elite Finisher"
    if finish_rate >= 0.55:
        return "High Finisher"
    if finish_rate >= 0.35:
        return "Balanced"
    return "Decision Fighter"


def _sos_label(opp_win_pct: float) -> str:
    if opp_win_pct >= 0.65:
        return "Elite Competition"
    if opp_win_pct >= 0.50:
        return "Strong Competition"
    if opp_win_pct >= 0.35:
        return "Moderate Competition"
    return "Developing Competition"


def _style_archetype(
    sig_per_min: float,
    td_rate: float,
    td_per_15: float,
    control_per_15: float,
    finish_rate: float,
) -> str:
    is_grappler = td_rate >= 0.5 or control_per_15 >= 60
    is_striker = sig_per_min >= 4.0 and td_per_15 < 3.0
    is_finisher = finish_rate >= 0.6
    is_high_volume = sig_per_min >= 5.0

    if is_grappler and control_per_15 >= 80 and is_finisher:
        return "Dominant Wrestler"
    if is_grappler and is_finisher:
        return "Submission Hunter"
    if is_grappler:
        return "Elite Grappler"
    if is_striker and is_finisher and is_high_volume:
        return "Pressure Striker"
    if is_striker and is_finisher:
        return "Power Striker"
    if is_striker and is_high_volume:
        return "High-Volume Striker"
    if sig_per_min >= 3.0 and td_per_15 >= 2.0:
        return "Well-Rounded"
    return "Technical Fighter"


def _rating_percentile(fighter_id: str, all_division_rows: list[dict]) -> float:
    """Position of this fighter in their division on a 0–100 scale (100 = top)."""
    if not all_division_rows:
        return 50.0
    ratings = rate_all(all_division_rows)
    this_rating = next((r.rating for r in ratings if r.fighter_id == fighter_id), None)
    if this_rating is None:
        return 50.0
    below = sum(1 for r in ratings if r.rating < this_rating)
    return round((below / len(ratings)) * 100.0, 1)


# ── Public API ────────────────────────────────────────────────────────────────


def build_profile(row: dict, all_division_rows: list[dict]) -> FighterProfile:
    """Build a FighterProfile from a features row and all rows in the same division."""
    rating = rate_fighter(row)

    days = _f(row, "activity_recency_days", 999.0)
    streak = int(_f(row, "win_streak"))
    last5 = _f(row, "last_5_win_pct")
    sig = _f(row, "sig_str_diff_per_min")
    td_rate = _f(row, "td_rate")
    td_per_15 = _f(row, "td_attempts_per_15")
    ctrl = _f(row, "control_per_15")
    finish = _f(row, "finish_rate")
    opp = _f(row, "opponent_recent_win_pct_avg", 0.5)

    percentile = _rating_percentile(row.get("fighter_id", ""), all_division_rows)

    return FighterProfile(
        fighter_id=row.get("fighter_id", ""),
        name=row.get("name", "Unknown"),
        division=row.get("weight_class", "Unknown"),
        rating=rating,
        rating_percentile=percentile,
        days_since_last_fight=days,
        activity_status=_activity_status(days),
        win_streak=streak,
        last_5_win_pct=last5,
        momentum=_momentum(streak, last5, days),
        sig_str_per_min=sig,
        striking_label=_striking_label(sig),
        td_rate=td_rate,
        td_per_15=td_per_15,
        control_per_15=ctrl,
        grappling_label=_grappling_label(td_rate, td_per_15, ctrl),
        finish_rate=finish,
        finish_label=_finish_label(finish),
        opp_win_pct_avg=opp,
        sos_label=_sos_label(opp),
        style_archetype=_style_archetype(sig, td_rate, td_per_15, ctrl, finish),
        consistency_score=_consistency_score(last5, streak, days),
        volatility_label=_volatility_label(last5, finish),
    )


def profile_to_dict(p: FighterProfile) -> dict:
    """Serialize a FighterProfile to a JSON-safe dict."""
    return {
        "fighter_id": p.fighter_id,
        "name": p.name,
        "division": p.division,
        "rating": p.rating.rating,
        "rating_percentile": p.rating_percentile,
        "activity_status": p.activity_status,
        "days_since_last_fight": p.days_since_last_fight,
        "win_streak": p.win_streak,
        "last_5_win_pct": p.last_5_win_pct,
        "momentum": p.momentum,
        "sig_str_per_min": p.sig_str_per_min,
        "striking_label": p.striking_label,
        "td_rate": p.td_rate,
        "td_per_15": p.td_per_15,
        "control_per_15": p.control_per_15,
        "grappling_label": p.grappling_label,
        "finish_rate": p.finish_rate,
        "finish_label": p.finish_label,
        "opp_win_pct_avg": p.opp_win_pct_avg,
        "sos_label": p.sos_label,
        "style_archetype": p.style_archetype,
        "consistency_score": p.consistency_score,
        "volatility_label": p.volatility_label,
        "rating_components": {
            "activity": p.rating.activity_score,
            "form": p.rating.form_score,
            "efficiency": p.rating.efficiency_score,
            "opponent_quality": p.rating.opponent_quality_score,
            "finish_ability": p.rating.finish_ability_score,
        },
    }


def format_profile_terminal(p: FighterProfile) -> str:
    """Render a FighterProfile as a formatted terminal string."""
    bar_width = 20
    r = p.rating.rating
    filled = round((r / 10.0) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)

    lines = [
        "",
        f"  {'=' * 52}",
        f"  Fighter Profile: {p.name}",
        f"  {'=' * 52}",
        f"  Division:     {p.division}",
        f"  Rating:       {r:.1f} / 10  [{bar}]  (Top {100 - p.rating_percentile:.0f}%)",
        f"  Archetype:    {p.style_archetype}",
        "",
        f"  ACTIVITY      {p.activity_status}  (last fight {p.days_since_last_fight:.0f} days ago)",
        f"  MOMENTUM      {p.momentum}  (win streak: {p.win_streak} | last 5: {p.last_5_win_pct:.0%})",
        f"  RELIABILITY   {p.volatility_label}  (consistency: {p.consistency_score:.3f})",
        f"  STRIKING      {p.striking_label}  ({p.sig_str_per_min:.1f} sig strikes/min)",
        f"  GRAPPLING     {p.grappling_label}  (TD rate: {p.td_rate:.2f} | control: {p.control_per_15:.0f}s/15min)",
        f"  FINISHING     {p.finish_label}  ({p.finish_rate:.0%} finish rate)",
        f"  COMPETITION   {p.sos_label}  (avg opp win %: {p.opp_win_pct_avg:.2f})",
        "",
        "  Rating components:",
        f"    Activity:        {p.rating.activity_score:.3f}",
        f"    Form:            {p.rating.form_score:.3f}",
        f"    Efficiency:      {p.rating.efficiency_score:.3f}",
        f"    Opp. Quality:    {p.rating.opponent_quality_score:.3f}",
        f"    Finish Ability:  {p.rating.finish_ability_score:.3f}",
        "",
    ]
    return "\n".join(lines)


def format_profile_markdown(p: FighterProfile) -> str:
    """Render a FighterProfile as a Markdown report string."""
    from datetime import datetime

    ts = datetime.now().isoformat(timespec="seconds")
    lines = [
        f"# Fighter Profile: {p.name}",
        "",
        f"**Division:** {p.division}  ",
        f"**Generated:** {ts}",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Rating | {p.rating.rating:.1f} / 10 (Top {100 - p.rating_percentile:.0f}%) |",
        f"| Archetype | {p.style_archetype} |",
        f"| Activity | {p.activity_status} ({p.days_since_last_fight:.0f} days since last fight) |",
        f"| Momentum | {p.momentum} (streak: {p.win_streak} \\| last 5: {p.last_5_win_pct:.0%}) |",
        f"| Reliability | {p.volatility_label} (consistency: {p.consistency_score:.3f}) |",
        f"| Striking | {p.striking_label} ({p.sig_str_per_min:.1f} sig/min) |",
        f"| Grappling | {p.grappling_label} (TD rate: {p.td_rate:.2f} \\| control: {p.control_per_15:.0f}s/15min) |",
        f"| Finishing | {p.finish_label} ({p.finish_rate:.0%}) |",
        f"| Competition | {p.sos_label} (avg opp win %: {p.opp_win_pct_avg:.2f}) |",
        "",
        "## Rating Components",
        "",
        "| Component | Score |",
        "|-----------|-------|",
        f"| Activity (25%) | {p.rating.activity_score:.3f} |",
        f"| Form (25%) | {p.rating.form_score:.3f} |",
        f"| Efficiency (20%) | {p.rating.efficiency_score:.3f} |",
        f"| Opponent Quality (15%) | {p.rating.opponent_quality_score:.3f} |",
        f"| Finish Ability (15%) | {p.rating.finish_ability_score:.3f} |",
        f"| **Composite (0–10)** | **{p.rating.rating:.3f}** |",
        "",
    ]
    return "\n".join(lines)
