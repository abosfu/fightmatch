"""Test rank and score (deterministic)."""

from pathlib import Path
import tempfile
import csv

import pytest

from fightmatch.config import MatchConfig
from fightmatch.match.rank import rank_score, load_features_csv, rank_by_division
from fightmatch.match.score import matchup_score, select_matchups
from fightmatch.match.explain import explain_matchup


def test_rank_score():
    config = MatchConfig()
    row = {
        "fighter_id": "f1",
        "activity_recency_days": 90,
        "win_streak": 2,
        "last_5_win_pct": 0.8,
        "opponent_recent_win_pct_avg": 0.6,
        "finish_rate": 0.4,
    }
    s = rank_score(row, config)
    assert s > 0
    row2 = {**row, "activity_recency_days": 800}
    s2 = rank_score(row2, config)
    assert s2 < s


def test_load_features_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("fighter_id,name,weight_class,activity_recency_days,win_streak,last_5_win_pct,sig_str_diff_per_min,td_rate,td_attempts_per_15,control_per_15,finish_rate,opponent_recent_win_pct_avg\n")
        f.write("f1,Alice,Lightweight,60,2,0.8,5.0,0.5,3.0,30,0.4,0.6\n")
        f.write("f2,Bob,Lightweight,120,1,0.6,4.0,0.3,2.0,20,0.2,0.5\n")
        path = Path(f.name)
    try:
        rows = load_features_csv(path)
        assert len(rows) == 2
        assert rows[0]["win_streak"] == 2.0
        assert rows[0]["weight_class"] == "Lightweight"
    finally:
        path.unlink(missing_ok=True)


def test_rank_by_division():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        w = csv.DictWriter(
            f,
            fieldnames=["fighter_id", "name", "weight_class", "activity_recency_days", "win_streak", "last_5_win_pct",
                        "sig_str_diff_per_min", "td_rate", "td_attempts_per_15", "control_per_15", "finish_rate", "opponent_recent_win_pct_avg"],
        )
        w.writeheader()
        w.writerow({"fighter_id": "f1", "name": "A", "weight_class": "Lightweight", "activity_recency_days": 60, "win_streak": 2, "last_5_win_pct": 0.8, "sig_str_diff_per_min": 5, "td_rate": 0.5, "td_attempts_per_15": 3, "control_per_15": 30, "finish_rate": 0.4, "opponent_recent_win_pct_avg": 0.6})
        w.writerow({"fighter_id": "f2", "name": "B", "weight_class": "Lightweight", "activity_recency_days": 90, "win_streak": 1, "last_5_win_pct": 0.6, "sig_str_diff_per_min": 4, "td_rate": 0.3, "td_attempts_per_15": 2, "control_per_15": 20, "finish_rate": 0.2, "opponent_recent_win_pct_avg": 0.5})
        w.writerow({"fighter_id": "f3", "name": "C", "weight_class": "Heavyweight", "activity_recency_days": 100, "win_streak": 0, "last_5_win_pct": 0.4, "sig_str_diff_per_min": 3, "td_rate": 0.2, "td_attempts_per_15": 1, "control_per_15": 10, "finish_rate": 0.1, "opponent_recent_win_pct_avg": 0.4})
        path = Path(f.name)
    try:
        ranked = rank_by_division(path, "Lightweight", top_n=5)
        assert len(ranked) == 2
        assert ranked[0][0]["fighter_id"] == "f1"
        ranked_all = rank_by_division(path, "", top_n=10)
        assert len(ranked_all) == 3
    finally:
        path.unlink(missing_ok=True)


def test_matchup_score():
    config = MatchConfig()
    fa = {"fighter_id": "a", "activity_recency_days": 90, "sig_str_diff_per_min": 6, "td_attempts_per_15": 1, "finish_rate": 0.5}
    fb = {"fighter_id": "b", "activity_recency_days": 100, "sig_str_diff_per_min": 3, "td_attempts_per_15": 4, "finish_rate": 0.3}
    sc = matchup_score(fa, fb, 2.0, 1.8, config, recent_bout_pair=False)
    assert sc > 0
    sc_rematch = matchup_score(fa, fb, 2.0, 1.8, config, recent_bout_pair=True)
    assert sc_rematch < sc


def test_select_matchups():
    config = MatchConfig()
    ranked = [
        ({"fighter_id": "f1", "name": "A", "activity_recency_days": 60, "sig_str_diff_per_min": 5, "td_attempts_per_15": 1, "finish_rate": 0.4}, 2.0),
        ({"fighter_id": "f2", "name": "B", "activity_recency_days": 90, "sig_str_diff_per_min": 4, "td_attempts_per_15": 3, "finish_rate": 0.2}, 1.8),
    ]
    matchups = select_matchups(ranked, top_n=5, config=config)
    assert len(matchups) == 1
    assert matchups[0][0]["fighter_id"] in ("f1", "f2")
    assert matchups[0][1]["fighter_id"] in ("f1", "f2")


def test_explain_matchup():
    fa = {"fighter_id": "a", "win_streak": 2, "opponent_recent_win_pct_avg": 0.6, "sig_str_diff_per_min": 5, "td_attempts_per_15": 1, "activity_recency_days": 90}
    fb = {"fighter_id": "b", "win_streak": 1, "opponent_recent_win_pct_avg": 0.5, "sig_str_diff_per_min": 3, "td_attempts_per_15": 4, "activity_recency_days": 100}
    reasons = explain_matchup(fa, fb, 2.0, 1.8, rank_positions=(1, 2))
    assert len(reasons) >= 3
    assert len(reasons) <= 6
