"""Tests for Phase 2 features: consistency, landscape, explain, what-if."""

from __future__ import annotations

import pytest

from fightmatch.analytics.consistency import consistency_score, volatility_label
from fightmatch.analytics.landscape import (
    DivisionLandscape,
    build_landscape,
    format_landscape_terminal,
)
from fightmatch.analytics.rating import FighterRating, rate_fighter
from fightmatch.engine.explain import explain_matchup_narrative
from fightmatch.engine.promoter import score_matchup
from fightmatch.engine.simulate import simulate
from fightmatch.engine.whatif import (
    SCENARIOS,
    WhatIfResult,
    format_whatif_terminal,
    run_whatif,
)


# ── Shared fixtures ────────────────────────────────────────────────────────────

def _row(
    fighter_id: str = "f1",
    name: str = "Fighter A",
    weight_class: str = "Welterweight",
    activity_recency_days: float = 90,
    win_streak: float = 2,
    last_5_win_pct: float = 0.8,
    sig_str_diff_per_min: float = 4.5,
    td_rate: float = 0.5,
    td_attempts_per_15: float = 4.0,
    control_per_15: float = 60.0,
    finish_rate: float = 0.6,
    opponent_recent_win_pct_avg: float = 0.6,
) -> dict:
    return {
        "fighter_id": fighter_id,
        "name": name,
        "weight_class": weight_class,
        "activity_recency_days": activity_recency_days,
        "win_streak": win_streak,
        "last_5_win_pct": last_5_win_pct,
        "sig_str_diff_per_min": sig_str_diff_per_min,
        "td_rate": td_rate,
        "td_attempts_per_15": td_attempts_per_15,
        "control_per_15": control_per_15,
        "finish_rate": finish_rate,
        "opponent_recent_win_pct_avg": opponent_recent_win_pct_avg,
    }


def _rating(
    fighter_id: str = "f1",
    name: str = "Fighter A",
    division: str = "Welterweight",
    activity_score: float = 0.8,
    form_score: float = 0.7,
    efficiency_score: float = 0.6,
    opponent_quality_score: float = 0.5,
    finish_ability_score: float = 0.6,
) -> FighterRating:
    composite = (
        0.25 * activity_score
        + 0.25 * form_score
        + 0.20 * efficiency_score
        + 0.15 * opponent_quality_score
        + 0.15 * finish_ability_score
    )
    return FighterRating(
        fighter_id=fighter_id,
        name=name,
        division=division,
        activity_score=activity_score,
        form_score=form_score,
        efficiency_score=efficiency_score,
        opponent_quality_score=opponent_quality_score,
        finish_ability_score=finish_ability_score,
        rating=round(composite * 10.0, 3),
    )


# ── consistency_score ─────────────────────────────────────────────────────────

class TestConsistencyScore:
    def test_all_zeros_returns_zero(self):
        assert consistency_score(0.0, 0, 730.0) == 0.0

    def test_perfect_input_returns_one(self):
        # 1.0 win_pct (50%), streak=3 (30%), 0 days (20%) → 1.0
        score = consistency_score(1.0, 3, 0.0)
        assert score == pytest.approx(1.0, abs=1e-4)

    def test_win_component_capped(self):
        # win_pct > 1.0 should be clamped
        score_a = consistency_score(1.5, 0, 730.0)
        score_b = consistency_score(1.0, 0, 730.0)
        assert score_a == score_b

    def test_win_component_negative_clamped(self):
        score = consistency_score(-0.5, 0, 730.0)
        assert score >= 0.0

    def test_streak_capped_at_three(self):
        score_3 = consistency_score(0.5, 3, 365.0)
        score_10 = consistency_score(0.5, 10, 365.0)
        assert score_3 == score_10

    def test_activity_zero_beyond_730(self):
        # Beyond 730 days, activity component should be 0
        score = consistency_score(0.0, 0, 800.0)
        assert score == 0.0

    def test_result_is_between_zero_and_one(self):
        for win_pct in [0.0, 0.3, 0.6, 1.0]:
            for streak in [0, 1, 5]:
                for days in [0, 180, 365, 730]:
                    s = consistency_score(win_pct, streak, days)
                    assert 0.0 <= s <= 1.0

    def test_result_is_rounded_to_four_decimals(self):
        score = consistency_score(0.7, 1, 200.0)
        assert score == round(score, 4)


# ── volatility_label ──────────────────────────────────────────────────────────

class TestVolatilityLabel:
    def test_stable(self):
        # winning + low finish rate
        assert volatility_label(0.80, 0.40) == "Stable"

    def test_high_risk_high_reward_elite_finisher(self):
        # high finish rate regardless of win pct
        assert volatility_label(0.40, 0.70) == "High-Risk / High-Reward"

    def test_high_risk_with_winning_record(self):
        # high finish rate + winning
        assert volatility_label(0.80, 0.70) == "High-Risk / High-Reward"

    def test_inconsistent(self):
        # low win rate + low finish rate
        assert volatility_label(0.20, 0.30) == "Inconsistent"

    def test_steady(self):
        # not winning, not elite finisher but covers the else branch
        # Actually per code: if not winning → "Inconsistent" is returned before "Steady"
        # "Steady" branch is dead under current logic; test the boundary
        result = volatility_label(0.55, 0.40)
        # 0.55 < 0.60 so not "winning"; 0.40 < 0.65 so not "elite_finisher"
        # → "Inconsistent"
        assert result == "Inconsistent"

    def test_exactly_at_winning_threshold(self):
        # 0.60 is the winning threshold
        assert volatility_label(0.60, 0.30) == "Stable"

    def test_exactly_at_elite_finisher_threshold(self):
        # 0.65 is the elite finisher threshold
        assert volatility_label(0.50, 0.65) == "High-Risk / High-Reward"


# ── build_landscape ───────────────────────────────────────────────────────────

class TestBuildLandscape:
    def test_empty_ratings_returns_defaults(self):
        ls = build_landscape("Welterweight", [])
        assert ls.division == "Welterweight"
        assert ls.fighter_count == 0
        assert ls.depth_score == 0.0
        assert ls.activity_level == "Low"
        assert ls.title_picture_clarity == "Developing"
        assert ls.logjam is False
        assert ls.top_rated_fighter == "N/A"
        assert ls.rating_spread == 0.0

    def test_single_fighter(self):
        r = _rating("f1", "Solo")
        ls = build_landscape("Bantamweight", [r])
        assert ls.fighter_count == 1
        assert ls.top_rated_fighter == "Solo"
        assert ls.title_picture_clarity == "Developing"  # < 2 fighters
        assert ls.logjam is False  # < 3 top-tier fighters

    def test_fighter_count_matches_input(self):
        ratings = [_rating(f"f{i}", f"Fighter {i}") for i in range(5)]
        ls = build_landscape("Flyweight", ratings)
        assert ls.fighter_count == 5

    def test_active_count_counts_activity_score_gte_half(self):
        # activity_score >= 0.5 means active
        active = _rating("a1", "Active", activity_score=0.8)
        inactive = _rating("a2", "Inactive", activity_score=0.3)
        ls = build_landscape("Lightweight", [active, inactive])
        assert ls.active_count == 1

    def test_depth_score_is_fraction_above_competitive_baseline(self):
        # depth_score = fraction of fighters with rating >= 5.0
        # rating = composite * 10; need composite >= 0.5
        high = _rating("h1", "High", activity_score=0.9, form_score=0.9,
                        efficiency_score=0.8, opponent_quality_score=0.7, finish_ability_score=0.8)
        low = _rating("l1", "Low", activity_score=0.1, form_score=0.1,
                       efficiency_score=0.1, opponent_quality_score=0.1, finish_ability_score=0.1)
        ls = build_landscape("Middleweight", [high, low])
        assert 0.0 <= ls.depth_score <= 1.0

    def test_activity_level_high(self):
        ratings = [
            _rating(f"f{i}", f"F{i}", activity_score=0.9) for i in range(3)
        ]
        ls = build_landscape("Welterweight", ratings)
        # All 3 have activity_score >= 0.5 → active_fraction = 1.0 → "High"
        assert ls.activity_level == "High"

    def test_activity_level_low(self):
        ratings = [
            _rating(f"f{i}", f"F{i}", activity_score=0.1) for i in range(3)
        ]
        ls = build_landscape("Welterweight", ratings)
        # All inactive → active_fraction = 0.0 → "Low"
        assert ls.activity_level == "Low"

    def test_title_picture_stagnant_when_top3_all_inactive(self):
        # activity_score < 0.5 for all top fighters → "Stagnant"
        ratings = [
            _rating(f"f{i}", f"F{i}", activity_score=0.3, form_score=0.8) for i in range(3)
        ]
        ls = build_landscape("Heavyweight", ratings)
        assert ls.title_picture_clarity == "Stagnant"

    def test_notes_is_list(self):
        r = _rating("f1", "Solo")
        ls = build_landscape("Strawweight", [r])
        assert isinstance(ls.notes, list)

    def test_rating_spread_is_max_minus_min(self):
        r1 = _rating("f1", "Top", form_score=1.0, activity_score=1.0)
        r2 = _rating("f2", "Bottom", form_score=0.0, activity_score=0.0)
        ls = build_landscape("Featherweight", [r1, r2])
        assert ls.rating_spread == pytest.approx(r1.rating - r2.rating, abs=0.01)


class TestFormatLandscapeTerminal:
    def test_returns_string(self):
        ls = build_landscape("Welterweight", [_rating("f1", "Solo")])
        result = format_landscape_terminal(ls)
        assert isinstance(result, str)

    def test_contains_division_name(self):
        ls = build_landscape("Strawweight", [_rating("f1", "Solo")])
        result = format_landscape_terminal(ls)
        assert "Strawweight" in result

    def test_contains_fighter_count(self):
        ls = build_landscape("Flyweight", [_rating(f"f{i}", f"F{i}") for i in range(4)])
        result = format_landscape_terminal(ls)
        assert "4" in result


# ── explain_matchup_narrative ─────────────────────────────────────────────────

class TestExplainMatchupNarrative:
    def _make_sim_ps(self, **sim_overrides):
        row_a = _row("f1", "Alpha", finish_rate=0.7)
        row_b = _row("f2", "Beta", finish_rate=0.3, activity_recency_days=400)
        sim = simulate(row_a, row_b, rank_pos_a=1, rank_pos_b=3, n_division_fighters=10)
        ps = score_matchup(sim, row_a, row_b)
        return sim, ps

    def test_returns_list(self):
        sim, ps = self._make_sim_ps()
        result = explain_matchup_narrative(sim, ps)
        assert isinstance(result, list)

    def test_returns_at_most_five_bullets(self):
        sim, ps = self._make_sim_ps()
        result = explain_matchup_narrative(sim, ps)
        assert len(result) <= 5

    def test_returns_at_least_one_bullet(self):
        sim, ps = self._make_sim_ps()
        result = explain_matchup_narrative(sim, ps)
        assert len(result) >= 1

    def test_all_bullets_are_strings(self):
        sim, ps = self._make_sim_ps()
        result = explain_matchup_narrative(sim, ps)
        assert all(isinstance(b, str) for b in result)

    def test_rematch_flag_produces_freshness_note(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        sim = simulate(row_a, row_b)
        ps = score_matchup(sim, row_a, row_b, is_recent_rematch=True)
        result = explain_matchup_narrative(sim, ps)
        freshness_bullets = [b for b in result if "freshness" in b.lower() or "recent matchup" in b.lower()]
        assert len(freshness_bullets) >= 1


# ── run_whatif ────────────────────────────────────────────────────────────────

class TestRunWhatif:
    def test_unknown_scenario_returns_none(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "nonexistent-scenario")
        assert result is None

    def test_returns_whatif_result(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "short-notice")
        assert isinstance(result, WhatIfResult)

    def test_all_scenarios_produce_result(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        for key in SCENARIOS:
            result = run_whatif(row_a, row_b, key)
            assert result is not None, f"Scenario '{key}' returned None"

    def test_scenario_name_matches(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "long-layoff")
        assert result.scenario == "long-layoff"

    def test_description_is_nonempty(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "win-streak-boost")
        assert result.description

    def test_deltas_computed_correctly(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "win-streak-boost")
        assert result.delta_rating == pytest.approx(
            result.scenario_rating_a - result.base_rating_a, abs=1e-4
        )
        assert result.delta_win_prob == pytest.approx(
            result.scenario_win_prob_a - result.base_win_prob_a, abs=1e-4
        )
        assert result.delta_promoter == pytest.approx(
            result.scenario_promoter_total - result.base_promoter_total, abs=1e-4
        )

    def test_short_notice_resets_activity_recency(self):
        row_a = _row("f1", "Alpha", activity_recency_days=300)
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "short-notice")
        # short-notice sets activity_recency_days to 14 (absolute)
        assert result.applied_changes["activity_recency_days"]["modified"] == 14.0

    def test_long_layoff_adds_days(self):
        row_a = _row("f1", "Alpha", activity_recency_days=100)
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "long-layoff")
        # long-layoff adds 365 days (delta)
        assert result.applied_changes["activity_recency_days"]["modified"] == pytest.approx(465.0)

    def test_recent_loss_penalty_resets_streak(self):
        row_a = _row("f1", "Alpha", win_streak=5)
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "recent-loss-penalty")
        # win_streak reset to 0 (absolute)
        assert result.applied_changes["win_streak"]["modified"] == 0.0

    def test_win_pct_clamped_to_one(self):
        # If last_5_win_pct is already 1.0 and we add 0.20, it should be clamped to 1.0
        row_a = _row("f1", "Alpha", last_5_win_pct=1.0)
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "win-streak-boost")
        assert result.applied_changes["last_5_win_pct"]["modified"] <= 1.0

    def test_promoter_tier_is_valid(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "short-notice")
        assert result.base_promoter_tier in {"Priority", "Strong", "Consider", "Pass"}
        assert result.scenario_promoter_tier in {"Priority", "Strong", "Consider", "Pass"}


class TestFormatWhatifTerminal:
    def test_returns_string(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "short-notice")
        output = format_whatif_terminal(result, "Alpha", "Beta")
        assert isinstance(output, str)

    def test_contains_scenario_name(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "long-layoff")
        output = format_whatif_terminal(result, "Alpha", "Beta")
        assert "long-layoff" in output

    def test_contains_fighter_name(self):
        row_a = _row("f1", "Alpha")
        row_b = _row("f2", "Beta")
        result = run_whatif(row_a, row_b, "short-notice")
        output = format_whatif_terminal(result, "Alpha", "Beta")
        assert "Alpha" in output


# ── SCENARIOS registry ────────────────────────────────────────────────────────

class TestScenariosRegistry:
    def test_all_required_scenarios_present(self):
        for key in ("short-notice", "long-layoff", "win-streak-boost", "recent-loss-penalty"):
            assert key in SCENARIOS

    def test_each_scenario_has_description(self):
        for key, scenario in SCENARIOS.items():
            assert "description" in scenario, f"Missing description in scenario '{key}'"
            assert scenario["description"]

    def test_each_scenario_has_changes(self):
        for key, scenario in SCENARIOS.items():
            assert "changes" in scenario, f"Missing changes in scenario '{key}'"
            assert scenario["changes"]

    def test_each_scenario_has_absolute_set(self):
        for key, scenario in SCENARIOS.items():
            assert "absolute" in scenario, f"Missing absolute in scenario '{key}'"
            assert isinstance(scenario["absolute"], (set, frozenset))
