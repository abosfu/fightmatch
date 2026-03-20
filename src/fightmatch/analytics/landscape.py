"""Division Landscape Analyzer.

Computes division-level competitive health from a list of FighterRating objects.

Outputs a DivisionLandscape with:
    depth_score          — fraction of fighters rated ≥ 5.0 (competitive baseline)
    activity_level       — High / Medium / Low
    title_picture_clarity — Clear / Contested / Stagnant / Developing
    logjam               — True if 3+ fighters are bunched within 0.8 rating points
    notes                — 2–4 narrative observation bullets
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fightmatch.analytics.rating import FighterRating


@dataclass
class DivisionLandscape:
    division: str
    fighter_count: int
    active_count: int             # activity_score ≥ 0.5  (proxy for ≤ 365 days)
    depth_score: float            # 0–1
    activity_level: str           # "High" | "Medium" | "Low"
    title_picture_clarity: str    # "Clear" | "Contested" | "Stagnant" | "Developing"
    logjam: bool
    top_rated_fighter: str
    rating_spread: float          # max − min rating
    notes: list[str] = field(default_factory=list)


def _activity_level(active_fraction: float) -> str:
    if active_fraction >= 0.66:
        return "High"
    if active_fraction >= 0.33:
        return "Medium"
    return "Low"


def _title_picture_clarity(sorted_ratings: list[FighterRating]) -> str:
    if len(sorted_ratings) < 2:
        return "Developing"
    # Stagnant: all of the top 3 have an activity proxy suggesting > 365 days out
    top_n = sorted_ratings[:min(3, len(sorted_ratings))]
    if all(r.activity_score < 0.50 for r in top_n):
        return "Stagnant"
    gap = sorted_ratings[0].rating - sorted_ratings[1].rating
    if gap >= 1.5:
        return "Clear"
    if gap <= 0.5:
        return "Contested"
    return "Developing"


def _logjam(sorted_ratings: list[FighterRating]) -> bool:
    """True if any 3 consecutive fighters in the top tier are within 0.8 rating."""
    top_tier = [r for r in sorted_ratings if r.rating >= 6.0]
    if len(top_tier) < 3:
        return False
    for i in range(len(top_tier) - 2):
        window = top_tier[i : i + 3]
        if window[0].rating - window[-1].rating <= 0.8:
            return True
    return False


def _build_notes(ls: DivisionLandscape) -> list[str]:
    notes: list[str] = []

    if ls.title_picture_clarity == "Clear":
        notes.append(
            f"Title picture is clear — {ls.top_rated_fighter} leads by a comfortable margin"
        )
    elif ls.title_picture_clarity == "Contested":
        notes.append(
            "Contested title picture — multiple fighters within striking distance of the top spot"
        )
    elif ls.title_picture_clarity == "Stagnant":
        notes.append(
            "Division appears stagnant — the leading contenders have all been inactive for an extended period"
        )
    else:
        notes.append("Division still developing — no clear separation between the top contenders")

    if ls.logjam:
        notes.append(
            "Contender logjam detected — several fighters are bunched within 0.8 rating points"
        )

    if ls.activity_level == "Low":
        notes.append(
            "Low division activity — more than two-thirds of fighters are semi-active or inactive"
        )
    elif ls.activity_level == "High":
        notes.append("High division activity — most fighters are competing regularly")

    if ls.depth_score >= 0.70:
        notes.append(
            f"Deep division — {ls.depth_score:.0%} of fighters rate above the competitive baseline"
        )
    elif ls.depth_score <= 0.30:
        notes.append("Shallow division — few fighters currently meet the competitive baseline")

    return notes


def build_landscape(division: str, ratings: list[FighterRating]) -> DivisionLandscape:
    """Build a DivisionLandscape from a list of FighterRatings for a single division."""
    if not ratings:
        ls = DivisionLandscape(
            division=division,
            fighter_count=0,
            active_count=0,
            depth_score=0.0,
            activity_level="Low",
            title_picture_clarity="Developing",
            logjam=False,
            top_rated_fighter="N/A",
            rating_spread=0.0,
            notes=["No fighters in this division."],
        )
        return ls

    sorted_ratings = sorted(ratings, key=lambda r: -r.rating)
    active_count = sum(1 for r in ratings if r.activity_score >= 0.50)
    competitive_count = sum(1 for r in ratings if r.rating >= 5.0)
    rating_vals = [r.rating for r in ratings]

    ls = DivisionLandscape(
        division=division,
        fighter_count=len(ratings),
        active_count=active_count,
        depth_score=round(competitive_count / len(ratings), 3),
        activity_level=_activity_level(active_count / len(ratings)),
        title_picture_clarity=_title_picture_clarity(sorted_ratings),
        logjam=_logjam(sorted_ratings),
        top_rated_fighter=sorted_ratings[0].name,
        rating_spread=round(max(rating_vals) - min(rating_vals), 3),
        notes=[],
    )
    ls.notes = _build_notes(ls)
    return ls


def format_landscape_terminal(ls: DivisionLandscape) -> str:
    logjam_str = "Yes" if ls.logjam else "No"
    lines = [
        f"  ── Division Snapshot: {ls.division} ──",
        f"  Fighters:        {ls.fighter_count}  ({ls.active_count} active)",
        f"  Depth score:     {ls.depth_score:.2f}",
        f"  Activity level:  {ls.activity_level}",
        f"  Title picture:   {ls.title_picture_clarity}",
        f"  Logjam:          {logjam_str}",
        f"  Rating spread:   {ls.rating_spread:.1f} pts  (top → bottom)",
    ]
    if ls.notes:
        lines.append("  Observations:")
        for note in ls.notes:
            lines.append(f"    • {note}")
    return "\n".join(lines)
