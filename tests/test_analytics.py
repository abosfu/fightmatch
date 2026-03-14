"""Tests for the fighter analytics: rating engine and profile builder."""

from __future__ import annotations

import pytest

from fightmatch.analytics.rating import rate_fighter, rate_all, FighterRating
from fightmatch.analytics.profile import (
    build_profile,
    profile_to_dict,
    format_profile_terminal,
    _activity_status,
    _momentum,
    _striking_label,
    _grappling_label,
    _finish_label,
    _sos_label,
    _style_archetype,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_row(
    fighter_id: str = "f1",
    name: str = "Test Fighter",
    weight_class: str = "Welterweight",
    activity_recency_days: float = 90,
    win_streak: float = 3,
    last_5_win_pct: float = 0.8,
    sig_str_diff_per_min: float = 4.5,
    td_rate: float = 0.5,
    td_attempts_per_15: float = 5.0,
    control_per_15: float = 60.0,
    finish_rate: float = 0.7,
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


# ── rating engine ─────────────────────────────────────────────────────────────

class TestRateFighter:
    def test_returns_fighter_rating(self):
        row = _make_row()
        r = rate_fighter(row)
        assert isinstance(r, FighterRating)

    def test_rating_in_range(self):
        row = _make_row()
        r = rate_fighter(row)
        assert 0.0 <= r.rating <= 10.0

    def test_component_scores_in_range(self):
        row = _make_row()
        r = rate_fighter(row)
        for score in (r.activity_score, r.form_score, r.efficiency_score,
                      r.opponent_quality_score, r.finish_ability_score):
            assert 0.0 <= score <= 1.0

    def test_active_fighter_has_high_activity_score(self):
        row = _make_row(activity_recency_days=30)
        r = rate_fighter(row)
        assert r.activity_score > 0.90

    def test_inactive_fighter_has_low_activity_score(self):
        row = _make_row(activity_recency_days=730)
        r = rate_fighter(row)
        assert r.activity_score < 0.30

    def test_better_fighter_ranks_higher(self):
        good = _make_row(
            fighter_id="good",
            activity_recency_days=60,
            win_streak=5,
            last_5_win_pct=0.9,
            sig_str_diff_per_min=6.0,
            td_rate=0.7,
            finish_rate=0.85,
            opponent_recent_win_pct_avg=0.70,
        )
        poor = _make_row(
            fighter_id="poor",
            activity_recency_days=700,
            win_streak=0,
            last_5_win_pct=0.2,
            sig_str_diff_per_min=1.0,
            td_rate=0.1,
            finish_rate=0.05,
            opponent_recent_win_pct_avg=0.25,
        )
        assert rate_fighter(good).rating > rate_fighter(poor).rating

    def test_handles_missing_values_gracefully(self):
        row = {"fighter_id": "x", "name": "Empty", "weight_class": "W"}
        r = rate_fighter(row)
        assert 0.0 <= r.rating <= 10.0

    def test_handles_none_values_gracefully(self):
        row = _make_row()
        row["win_streak"] = None
        row["finish_rate"] = None
        r = rate_fighter(row)
        assert 0.0 <= r.rating <= 10.0

    def test_rating_is_deterministic(self):
        row = _make_row()
        assert rate_fighter(row).rating == rate_fighter(row).rating


class TestRateAll:
    def test_rate_all_preserves_order(self):
        rows = [_make_row(fighter_id=f"f{i}") for i in range(5)]
        ratings = rate_all(rows)
        assert len(ratings) == 5
        for i, r in enumerate(ratings):
            assert r.fighter_id == f"f{i}"

    def test_rate_all_empty(self):
        assert rate_all([]) == []


# ── label helpers ─────────────────────────────────────────────────────────────

class TestLabels:
    def test_activity_status(self):
        assert _activity_status(90) == "Active"
        assert _activity_status(270) == "Semi-Active"
        assert _activity_status(500) == "Inactive"

    def test_momentum(self):
        assert _momentum(3, 0.8, 90) == "Rising"
        assert _momentum(1, 0.6, 200) == "Steady"
        assert _momentum(0, 0.2, 400) == "Declining"

    def test_striking_label(self):
        assert _striking_label(6.0) == "High-Volume"
        assert _striking_label(4.0) == "Technical"
        assert _striking_label(2.5) == "Average"
        assert _striking_label(0.5) == "Limited"

    def test_grappling_label(self):
        assert _grappling_label(0.6, 5.0, 80.0) == "Dominant Grappler"
        assert _grappling_label(0.5, 4.5, 30.0) == "Active Wrestler"
        assert _grappling_label(0.2, 2.5, 25.0) == "Balanced"
        assert _grappling_label(0.1, 0.5, 5.0) == "Striker"

    def test_finish_label(self):
        assert _finish_label(0.80) == "Elite Finisher"
        assert _finish_label(0.60) == "High Finisher"
        assert _finish_label(0.40) == "Balanced"
        assert _finish_label(0.20) == "Decision Fighter"

    def test_sos_label(self):
        assert _sos_label(0.70) == "Elite Competition"
        assert _sos_label(0.55) == "Strong Competition"
        assert _sos_label(0.40) == "Moderate Competition"
        assert _sos_label(0.20) == "Developing Competition"

    def test_style_archetype_grappler(self):
        archetype = _style_archetype(
            sig_per_min=2.0, td_rate=0.65, td_per_15=6.0,
            control_per_15=90.0, finish_rate=0.7,
        )
        assert archetype in ("Dominant Wrestler", "Submission Hunter", "Elite Grappler")

    def test_style_archetype_striker(self):
        archetype = _style_archetype(
            sig_per_min=5.5, td_rate=0.1, td_per_15=0.5,
            control_per_15=2.0, finish_rate=0.7,
        )
        assert "Striker" in archetype


# ── profile builder ──────────────────────────────────────────────────────────

class TestBuildProfile:
    def test_build_profile_returns_fighter_profile(self):
        row = _make_row()
        division_rows = [row, _make_row(fighter_id="f2", win_streak=1)]
        profile = build_profile(row, division_rows)
        assert profile.fighter_id == "f1"
        assert profile.name == "Test Fighter"
        assert profile.division == "Welterweight"

    def test_rating_percentile_top_fighter(self):
        best = _make_row(fighter_id="best", win_streak=5, last_5_win_pct=0.9,
                         activity_recency_days=30, finish_rate=0.9)
        worst = _make_row(fighter_id="worst", win_streak=0, last_5_win_pct=0.1,
                          activity_recency_days=700, finish_rate=0.0)
        profile_best = build_profile(best, [best, worst])
        profile_worst = build_profile(worst, [best, worst])
        assert profile_best.rating_percentile > profile_worst.rating_percentile

    def test_profile_to_dict_has_required_keys(self):
        row = _make_row()
        profile = build_profile(row, [row])
        d = profile_to_dict(profile)
        for key in ("fighter_id", "name", "division", "rating", "rating_percentile",
                    "activity_status", "momentum", "striking_label", "grappling_label",
                    "finish_label", "sos_label", "style_archetype", "rating_components"):
            assert key in d, f"Missing key: {key}"

    def test_format_profile_terminal_returns_string(self):
        row = _make_row()
        profile = build_profile(row, [row])
        text = format_profile_terminal(profile)
        assert isinstance(text, str)
        assert "Test Fighter" in text
        assert "Welterweight" in text
