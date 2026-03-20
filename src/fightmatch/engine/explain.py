"""Explainability Layer.

Converts promoter score components and simulation metrics into human-readable
narrative bullets. Deterministic, rule-based — no NLP or ML.

Complements MatchupSimulation.key_factors (per-fighter stat signals) with
matchup-quality signals drawn from the PromoterScore components.
"""

from __future__ import annotations

from fightmatch.engine.simulate import MatchupSimulation
from fightmatch.engine.promoter import PromoterScore


def explain_matchup_narrative(sim: MatchupSimulation, ps: PromoterScore) -> list[str]:
    """
    Generate 3–5 narrative bullets explaining the matchup quality.

    Covers: competitiveness, style contrast, divisional relevance,
    activity readiness, freshness, and fan interest.
    """
    notes: list[str] = []

    # ── Competitiveness ───────────────────────────────────────────────────────
    if ps.competitiveness >= 0.85:
        notes.append(
            f"Genuine toss-up — {sim.fighter_a} and {sim.fighter_b} are virtually "
            f"even on the ratings (competitiveness {ps.competitiveness:.2f})"
        )
    elif ps.competitiveness >= 0.65:
        notes.append(
            "Competitive matchup — ratings are close enough that either outcome is plausible"
        )
    elif ps.competitiveness >= 0.40:
        notes.append(
            "One fighter holds a clear rating edge; upset potential exists but the gap is meaningful"
        )
    else:
        notes.append(
            "Significant rating disparity — this is a developmental matchup rather than a title-level fight"
        )

    # ── Style contrast ────────────────────────────────────────────────────────
    if ps.style_interest >= 0.55:
        notes.append(
            f"Strong style clash ({sim.style_contrast_label}) — divergent fighting "
            "approaches add strategic intrigue"
        )
    elif ps.style_interest >= 0.35:
        notes.append(
            f"Moderate style contrast ({sim.style_contrast_label}) — distinct but "
            "not extreme differences in approach"
        )

    # ── Divisional relevance / rank impact ────────────────────────────────────
    if ps.divisional_relevance >= 0.80:
        notes.append(
            f"Title-eliminator territory — both fighters rank near the top of the "
            f"division ({sim.rank_impact_label})"
        )
    elif ps.divisional_relevance >= 0.55:
        notes.append(
            "High divisional stakes — a win here meaningfully reshapes the contender picture"
        )
    elif ps.divisional_relevance >= 0.30:
        notes.append(
            "Contender-level fight — outcome will influence the lower half of the rankings"
        )

    # ── Activity readiness ────────────────────────────────────────────────────
    if ps.activity_readiness < 0.50:
        notes.append(
            "Activity concern — one or both fighters have been inactive for an extended "
            "period; booking risk is elevated"
        )
    elif ps.activity_readiness >= 0.90:
        notes.append(
            "Both fighters are currently active — no readiness concerns for near-term booking"
        )

    # ── Freshness (rematch flag) ───────────────────────────────────────────────
    if ps.freshness == 0.0:
        notes.append(
            "Recent matchup history between these two reduces freshness; "
            "consider the promotional narrative before booking"
        )

    # ── Fan interest proxy ────────────────────────────────────────────────────
    if ps.fan_interest >= 0.60:
        notes.append(
            f"High finishing ability on both sides (fan interest proxy: {ps.fan_interest:.2f}) "
            "— stoppage probability supports pay-per-view appeal"
        )

    return notes[:5]
