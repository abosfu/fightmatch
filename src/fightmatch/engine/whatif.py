"""What-If Scenario Engine.

Applies a predefined scenario to Fighter A's feature row and re-runs the
matchup simulation to show how the outcome shifts.  All scenarios are
deterministic and rule-based — no ML or external data required.

Available scenarios
-------------------
short-notice        Fighter A accepts on 14-day notice (activity reset, form penalty)
long-layoff         Fighter A returning after a long absence (+365 days inactivity)
win-streak-boost    Fighter A on a hypothetical 3-fight win streak (+form)
recent-loss-penalty Fighter A coming off a loss (streak reset, reduced win rate)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fightmatch.engine.simulate import simulate
from fightmatch.engine.promoter import score_matchup


# ── Scenario registry ─────────────────────────────────────────────────────────

# Each entry:
#   description  — human-readable label
#   changes      — {field: value}; value is an absolute target when the field is
#                  listed in `absolute`, otherwise it is a delta (+/−)
#   absolute     — set of field names that are set to the exact value (not delta)

SCENARIOS: dict[str, dict] = {
    "short-notice": {
        "description": "Fighter A accepts on short notice (recency reset to 14 days, −10% form)",
        "changes": {"activity_recency_days": 14, "last_5_win_pct": -0.10},
        "absolute": {"activity_recency_days"},
    },
    "long-layoff": {
        "description": "Fighter A returning from a long layoff (+365 days added to inactivity)",
        "changes": {"activity_recency_days": 365},
        "absolute": set(),
    },
    "win-streak-boost": {
        "description": "Fighter A on a hypothetical 3-fight win streak (+2 fights, +20% form)",
        "changes": {"win_streak": 2, "last_5_win_pct": 0.20},
        "absolute": set(),
    },
    "recent-loss-penalty": {
        "description": "Fighter A coming off a recent loss (streak reset to 0, −20% recent form)",
        "changes": {"win_streak": 0, "last_5_win_pct": -0.20},
        "absolute": {"win_streak"},
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

_RATIO_FIELDS = {"last_5_win_pct", "td_rate", "finish_rate"}


def _f(row: dict, key: str, default: float = 0.0) -> float:
    val = row.get(key, default)
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _apply_scenario(row: dict, scenario_key: str) -> tuple[dict, dict]:
    """
    Apply scenario adjustments to a feature row (non-destructive).

    Returns
    -------
    modified_row    copy of row with scenario values applied
    applied_changes {field: {"original": float, "modified": float}}
    """
    scenario = SCENARIOS[scenario_key]
    changes: dict = scenario["changes"]
    absolute: set = scenario["absolute"]

    modified = dict(row)
    applied: dict = {}

    for field, value in changes.items():
        original = _f(row, field, 0.0)
        if field in absolute:
            new_val = float(value)
        else:
            new_val = original + float(value)

        # Clamp ratio fields to [0, 1]
        if field in _RATIO_FIELDS:
            new_val = max(0.0, min(1.0, new_val))
        else:
            new_val = max(0.0, new_val)

        modified[field] = new_val
        applied[field] = {"original": round(original, 4), "modified": round(new_val, 4)}

    return modified, applied


# ── Public API ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class WhatIfResult:
    scenario: str
    description: str
    applied_changes: dict

    # Base simulation (unmodified fighter A)
    base_rating_a: float
    base_win_prob_a: float
    base_promoter_total: float
    base_promoter_tier: str

    # Scenario simulation (modified fighter A)
    scenario_rating_a: float
    scenario_win_prob_a: float
    scenario_promoter_total: float
    scenario_promoter_tier: str

    # Deltas (scenario − base)
    delta_rating: float
    delta_win_prob: float
    delta_promoter: float


def run_whatif(
    row_a: dict,
    row_b: dict,
    scenario_key: str,
    rank_pos_a: Optional[int] = None,
    rank_pos_b: Optional[int] = None,
    n_division_fighters: int = 0,
    is_recent_rematch: bool = False,
) -> Optional[WhatIfResult]:
    """
    Run a what-if analysis for the given scenario applied to Fighter A.

    Returns None if the scenario_key is not recognised.
    """
    if scenario_key not in SCENARIOS:
        return None

    scenario = SCENARIOS[scenario_key]

    # Base simulation
    base_sim = simulate(row_a, row_b, rank_pos_a, rank_pos_b, n_division_fighters)
    base_ps = score_matchup(base_sim, row_a, row_b, is_recent_rematch=is_recent_rematch)

    # Scenario simulation (fighter A modified)
    modified_a, applied = _apply_scenario(row_a, scenario_key)
    scenario_sim = simulate(modified_a, row_b, rank_pos_a, rank_pos_b, n_division_fighters)
    scenario_ps = score_matchup(
        scenario_sim, modified_a, row_b, is_recent_rematch=is_recent_rematch
    )

    return WhatIfResult(
        scenario=scenario_key,
        description=scenario["description"],
        applied_changes=applied,
        base_rating_a=base_sim.rating_a,
        base_win_prob_a=base_sim.win_prob_a,
        base_promoter_total=base_ps.total,
        base_promoter_tier=base_ps.tier,
        scenario_rating_a=scenario_sim.rating_a,
        scenario_win_prob_a=scenario_sim.win_prob_a,
        scenario_promoter_total=scenario_ps.total,
        scenario_promoter_tier=scenario_ps.tier,
        delta_rating=round(scenario_sim.rating_a - base_sim.rating_a, 4),
        delta_win_prob=round(scenario_sim.win_prob_a - base_sim.win_prob_a, 4),
        delta_promoter=round(scenario_ps.total - base_ps.total, 4),
    )


def format_whatif_terminal(result: WhatIfResult, name_a: str, name_b: str) -> str:
    """Render a WhatIfResult as a formatted terminal string."""

    def _sign(v: float) -> str:
        return f"+{v:.3f}" if v >= 0 else f"{v:.3f}"

    lines = [
        f"",
        f"  {'─' * 54}",
        f"  What-If Scenario: {result.scenario}",
        f"  {result.description}",
        f"  {'─' * 54}",
        f"  Fighter affected: {name_a}  (opponent: {name_b})",
        f"",
        f"  {'Metric':<28}  {'Base':>8}  {'Scenario':>10}  {'Delta':>9}",
        f"  {'─' * 60}",
        (
            f"  {'Rating (Fighter A)':<28}  {result.base_rating_a:>8.2f}"
            f"  {result.scenario_rating_a:>10.2f}  {_sign(result.delta_rating):>9}"
        ),
        (
            f"  {'Win Probability (A)':<28}  {result.base_win_prob_a:>7.0%}"
            f"  {result.scenario_win_prob_a:>9.0%}  {_sign(result.delta_win_prob):>9}"
        ),
        (
            f"  {'Promoter Score':<28}  {result.base_promoter_total:>8.3f}"
            f"  {result.scenario_promoter_total:>10.3f}  {_sign(result.delta_promoter):>9}"
        ),
        (
            f"  {'Promoter Tier':<28}  {result.base_promoter_tier:>8}"
            f"  {result.scenario_promoter_tier:>10}"
        ),
        f"",
    ]

    if result.applied_changes:
        lines.append(f"  Applied changes to {name_a}:")
        for field, vals in result.applied_changes.items():
            lines.append(
                f"    {field}: {vals['original']:.3f} → {vals['modified']:.3f}"
            )

    lines.append("")
    return "\n".join(lines)
