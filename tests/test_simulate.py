"""Tests for matchup simulation engine and promoter decision scoring."""

from __future__ import annotations

import pytest

from fightmatch.engine.simulate import (
    simulate,
    simulation_to_dict,
    format_simulation_terminal,
    MatchupSimulation,
    _win_probability,
    _competitiveness,
    _style_contrast,
)
from fightmatch.engine.promoter import (
    score_matchup,
    select_matchups_ranked,
    PromoterScore,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

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


# ── win probability ───────────────────────────────────────────────────────────

class TestWinProbability:
    def test_equal_ratings_gives_fifty_fifty(self):
        pa, pb = _win_probability(5.0, 5.0)
        assert abs(pa - 0.5) < 0.01
        assert abs(pb - 0.5) < 0.01

    def test_higher_rated_favored(self):
        pa, pb = _win_probability(8.0, 5.0)
        assert pa > 0.5
        assert pb < 0.5

    def test_probabilities_sum_to_one(self):
        for a, b in [(7.0, 4.0), (5.0, 5.0), (3.0, 9.0)]:
            pa, pb = _win_probability(a, b)
            assert abs(pa + pb - 1.0) < 1e-6

    def test_symmetry(self):
        pa, pb = _win_probability(7.0, 4.0)
        pb2, pa2 = _win_probability(4.0, 7.0)
        assert abs(pa - pa2) < 1e-6
        assert abs(pb - pb2) < 1e-6


class TestCompetitiveness:
    def test_fifty_fifty_is_fully_competitive(self):
        assert _competitiveness(0.5) == 1.0

    def test_complete_mismatch_is_zero(self):
        assert _competitiveness(1.0) == 0.0
        assert _competitiveness(0.0) == 0.0

    def test_slight_favorite_is_still_competitive(self):
        assert _competitiveness(0.6) > 0.7


class TestStyleContrast:
    def test_identical_profiles_have_low_contrast(self):
        row = _row()
        contrast = _style_contrast(row, row)
        assert contrast < 0.05

    def test_striker_vs_grappler_has_high_contrast(self):
        striker = _row(sig_str_diff_per_min=7.0, td_attempts_per_15=0.2, td_rate=0.1, control_per_15=2.0)
        grappler = _row(sig_str_diff_per_min=1.0, td_attempts_per_15=8.0, td_rate=0.7, control_per_15=100.0)
        contrast = _style_contrast(striker, grappler)
        assert contrast > 0.40


# ── simulation ────────────────────────────────────────────────────────────────

class TestSimulate:
    def test_returns_matchup_simulation(self):
        sim = simulate(_row("f1", "A"), _row("f2", "B"))
        assert isinstance(sim, MatchupSimulation)

    def test_fighter_names_correct(self):
        sim = simulate(_row(name="Jon"), _row(name="Stipe"))
        assert sim.fighter_a == "Jon"
        assert sim.fighter_b == "Stipe"

    def test_win_probs_sum_to_one(self):
        sim = simulate(_row("f1"), _row("f2"))
        assert abs(sim.win_prob_a + sim.win_prob_b - 1.0) < 1e-6

    def test_competitive_sim_has_balanced_probs(self):
        sim = simulate(
            _row("f1", last_5_win_pct=0.6, win_streak=2),
            _row("f2", last_5_win_pct=0.6, win_streak=2),
        )
        assert abs(sim.win_prob_a - 0.5) < 0.15

    def test_dominant_fighter_is_favored(self):
        elite = _row("elite", win_streak=5, last_5_win_pct=0.9,
                     activity_recency_days=30, finish_rate=0.9,
                     opponent_recent_win_pct_avg=0.8, sig_str_diff_per_min=6.0)
        novice = _row("novice", win_streak=0, last_5_win_pct=0.1,
                      activity_recency_days=700, finish_rate=0.1,
                      opponent_recent_win_pct_avg=0.2, sig_str_diff_per_min=1.0)
        sim = simulate(elite, novice)
        assert sim.win_prob_a > 0.65

    def test_rank_impact_uses_position(self):
        sim_top = simulate(_row("f1"), _row("f2"), rank_pos_a=1, rank_pos_b=2, n_division_fighters=10)
        sim_bottom = simulate(_row("f1"), _row("f2"), rank_pos_a=9, rank_pos_b=10, n_division_fighters=10)
        assert sim_top.rank_impact > sim_bottom.rank_impact

    def test_simulation_to_dict_structure(self):
        sim = simulate(_row("f1", "Alpha"), _row("f2", "Beta"))
        d = simulation_to_dict(sim)
        assert "fighter_a" in d
        assert "fighter_b" in d
        assert "win_probability" in d
        assert "fighter_a" in d["win_probability"]
        assert "fighter_b" in d["win_probability"]
        assert "competitiveness" in d
        assert "style_contrast" in d
        assert "rank_impact" in d
        assert "recommendation_summary" in d
        assert "key_factors" in d

    def test_format_simulation_terminal_returns_string(self):
        sim = simulate(_row("f1", "Alpha"), _row("f2", "Beta"))
        text = format_simulation_terminal(sim)
        assert isinstance(text, str)
        assert "Alpha" in text
        assert "Beta" in text


# ── promoter scoring ──────────────────────────────────────────────────────────

class TestPromoterScore:
    def test_returns_promoter_score(self):
        ra = _row("f1", "A")
        rb = _row("f2", "B")
        sim = simulate(ra, rb)
        ps = score_matchup(sim, ra, rb)
        assert isinstance(ps, PromoterScore)

    def test_total_in_range(self):
        ra = _row("f1")
        rb = _row("f2")
        sim = simulate(ra, rb)
        ps = score_matchup(sim, ra, rb)
        assert 0.0 <= ps.total <= 1.0

    def test_rematch_penalty(self):
        ra = _row("f1")
        rb = _row("f2")
        sim = simulate(ra, rb)
        ps_fresh = score_matchup(sim, ra, rb, is_recent_rematch=False)
        ps_rematch = score_matchup(sim, ra, rb, is_recent_rematch=True)
        assert ps_fresh.total > ps_rematch.total

    def test_tier_assigned(self):
        ra = _row("f1")
        rb = _row("f2")
        sim = simulate(ra, rb)
        ps = score_matchup(sim, ra, rb)
        assert ps.tier in ("Priority", "Strong", "Consider", "Pass")

    def test_higher_competitiveness_improves_score(self):
        # Identical fighters have 50/50 odds = max competitiveness
        ra = _row("f1", win_streak=2, last_5_win_pct=0.7)
        rb = _row("f2", win_streak=2, last_5_win_pct=0.7)

        # Mismatch: one clearly dominates
        rc = _row("f3", win_streak=5, last_5_win_pct=0.95,
                  activity_recency_days=30, finish_rate=0.95,
                  opponent_recent_win_pct_avg=0.9)
        rd = _row("f4", win_streak=0, last_5_win_pct=0.1,
                  activity_recency_days=600, finish_rate=0.0,
                  opponent_recent_win_pct_avg=0.1)

        sim_even = simulate(ra, rb)
        sim_skewed = simulate(rc, rd)

        ps_even = score_matchup(sim_even, ra, rb)
        ps_skewed = score_matchup(sim_skewed, rc, rd)
        assert ps_even.competitiveness > ps_skewed.competitiveness


class TestSelectMatchupsRanked:
    def test_returns_matchups(self):
        rated = [
            (_row("f1", "A"), 7.0),
            (_row("f2", "B"), 6.5),
            (_row("f3", "C"), 5.0),
        ]
        results = select_matchups_ranked(rated, top_n=3)
        assert len(results) >= 1

    def test_no_duplicate_fighters_in_selection(self):
        rated = [(_row(f"f{i}", f"Fighter{i}"), float(5 - i)) for i in range(5)]
        results = select_matchups_ranked(rated, top_n=3)
        seen_ids: set[str] = set()
        for row_a, row_b, sim, ps in results:
            id_a = row_a["fighter_id"]
            id_b = row_b["fighter_id"]
            assert id_a not in seen_ids
            assert id_b not in seen_ids
            seen_ids.add(id_a)
            seen_ids.add(id_b)

    def test_rematch_excluded_when_in_recent_pairs(self):
        ra = _row("f1", "A")
        rb = _row("f2", "B")
        rated = [(ra, 7.0), (rb, 6.8)]
        recent = {("f1", "f2")}
        results = select_matchups_ranked(rated, top_n=1, recent_pairs=recent)
        if results:
            ps = results[0][3]
            assert ps.freshness == 0.0

    def test_returns_empty_for_single_fighter(self):
        rated = [(_row("f1", "Solo"), 7.0)]
        results = select_matchups_ranked(rated, top_n=3)
        assert results == []
