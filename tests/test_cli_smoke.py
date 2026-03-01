"""CLI smoke tests with fixtures (no network)."""

import json
import tempfile
from pathlib import Path

import pytest

from fightmatch.data import build_dataset, build_features
from fightmatch.cli import cmd_build_dataset, cmd_features, cmd_recommend


def test_cli_build_dataset():
    """build-dataset runs and produces JSON/JSONL."""
    fixtures = Path(__file__).parent / "fixtures"
    raw = tempfile.mkdtemp()
    # Mimic raw layout: ufcstats/events/*.html, ufcstats/fights/*.html
    (Path(raw) / "ufcstats" / "events").mkdir(parents=True)
    (Path(raw) / "ufcstats" / "fights").mkdir(parents=True)
    (Path(raw) / "ufcstats" / "events" / "abc123.html").write_text((fixtures / "event_abc123.html").read_text())
    (Path(raw) / "ufcstats" / "fights" / "bout1.html").write_text((fixtures / "fight_bout1.html").read_text())
    out = tempfile.mkdtemp()
    build_dataset(Path(raw), Path(out))
    assert (Path(out) / "fighters.json").exists()
    assert (Path(out) / "events.json").exists()
    assert (Path(out) / "bouts.json").exists()
    assert (Path(out) / "stats.jsonl").exists()
    fighters = json.loads((Path(out) / "fighters.json").read_text())
    assert len(fighters) >= 2


def test_cli_features():
    """features runs and produces CSV."""
    processed = tempfile.mkdtemp()
    (Path(processed) / "fighters.json").write_text("[]")
    (Path(processed) / "events.json").write_text("[]")
    (Path(processed) / "bouts.json").write_text("[]")
    (Path(processed) / "stats.jsonl").write_text("")
    out_csv = Path(tempfile.mkdtemp()) / "features.csv"
    build_features(Path(processed), out_csv)
    assert out_csv.exists()
    content = out_csv.read_text()
    assert "fighter_id" in content


def test_cli_recommend_no_features():
    """recommend exits non-zero when features missing."""
    import argparse
    args = argparse.Namespace(
        features="nonexistent.csv",
        processed="data/processed",
        division="Lightweight",
        top=5,
        prioritize_contender_clarity=True,
        prioritize_action=False,
        allow_short_notice=False,
        avoid_rematch=True,
    )
    assert cmd_recommend(args) == 1


def test_cli_recommend_with_fake_features():
    """recommend runs and prints when features exist."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        f.write(b"fighter_id,name,weight_class,activity_recency_days,win_streak,last_5_win_pct,sig_str_diff_per_min,td_rate,td_attempts_per_15,control_per_15,finish_rate,opponent_recent_win_pct_avg\n")
        f.write(b"f1,Alice,Lightweight,60,2,0.8,5.0,0.5,3.0,30,0.4,0.6\n")
        f.write(b"f2,Bob,Lightweight,90,1,0.6,4.0,0.3,2.0,20,0.2,0.5\n")
        path = Path(f.name)
    try:
        import argparse
        args = argparse.Namespace(
            features=str(path),
            processed=tempfile.mkdtemp(),
            division="Lightweight",
            top=3,
            prioritize_contender_clarity=True,
            prioritize_action=False,
            allow_short_notice=False,
            avoid_rematch=True,
        )
        assert cmd_recommend(args) == 0
    finally:
        path.unlink(missing_ok=True)
