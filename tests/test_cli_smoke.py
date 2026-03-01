"""CLI smoke tests via subprocess (no internal imports, no network)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest


def _run_fightmatch(*args: str, cwd: Optional[str] = None, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """Run fightmatch CLI via same Python as test runner (no network if scrape is not invoked)."""
    cmd = [sys.executable, "-m", "fightmatch.cli"] + list(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
        env=env or {},
    )


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def raw_dir_from_fixtures(fixtures_dir: Path, tmp_path: Path) -> Path:
    """Build a raw dir with fixture HTML (ufcstats/events/*.html, ufcstats/fights/*.html)."""
    raw = tmp_path / "raw"
    (raw / "ufcstats" / "events").mkdir(parents=True)
    (raw / "ufcstats" / "fights").mkdir(parents=True)
    (raw / "ufcstats" / "events" / "abc123.html").write_text(
        (fixtures_dir / "event_abc123.html").read_text(),
        encoding="utf-8",
    )
    (raw / "ufcstats" / "fights" / "bout1.html").write_text(
        (fixtures_dir / "fight_bout1.html").read_text(),
        encoding="utf-8",
    )
    return raw


def test_cli_build_dataset_creates_output_files(raw_dir_from_fixtures: Path, tmp_path: Path) -> None:
    """build-dataset creates fighters.json, events.json, bouts.json, stats.jsonl."""
    out = tmp_path / "processed"
    proc = _run_fightmatch("build-dataset", "--raw", str(raw_dir_from_fixtures), "--out", str(out))
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert (out / "fighters.json").exists()
    assert (out / "events.json").exists()
    assert (out / "bouts.json").exists()
    assert (out / "stats.jsonl").exists()
    fighters = json.loads((out / "fighters.json").read_text())
    assert len(fighters) >= 2


def test_cli_features_creates_csv(raw_dir_from_fixtures: Path, tmp_path: Path) -> None:
    """features creates a CSV with expected header."""
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "fighters.json").write_text("[]")
    (processed / "events.json").write_text("[]")
    (processed / "bouts.json").write_text("[]")
    (processed / "stats.jsonl").write_text("")
    out_csv = tmp_path / "features.csv"
    proc = _run_fightmatch("features", "--in", str(processed), "--out", str(out_csv))
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert out_csv.exists()
    assert "fighter_id" in out_csv.read_text()


def test_cli_recommend_fails_when_features_missing(tmp_path: Path) -> None:
    """recommend exits non-zero when features file does not exist."""
    proc = _run_fightmatch(
        "recommend",
        "--features", str(tmp_path / "nonexistent.csv"),
        "--processed", str(tmp_path),
        "--division", "Lightweight",
        "--top", "5",
    )
    assert proc.returncode == 1


def test_cli_recommend_succeeds_for_division(tmp_path: Path) -> None:
    """recommend runs successfully for a division when features CSV exists."""
    features_csv = tmp_path / "features.csv"
    features_csv.write_text(
        "fighter_id,name,weight_class,activity_recency_days,win_streak,last_5_win_pct,"
        "sig_str_diff_per_min,td_rate,td_attempts_per_15,control_per_15,finish_rate,opponent_recent_win_pct_avg\n"
        "f1,Alice,Lightweight,60,2,0.8,5.0,0.5,3.0,30,0.4,0.6\n"
        "f2,Bob,Lightweight,90,1,0.6,4.0,0.3,2.0,20,0.2,0.5\n",
        encoding="utf-8",
    )
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "bouts.json").write_text("[]")
    proc = _run_fightmatch(
        "recommend",
        "--features", str(features_csv),
        "--processed", str(processed),
        "--division", "Lightweight",
        "--top", "3",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "FightMatch" in proc.stdout or "recommended" in proc.stdout.lower() or "vs" in proc.stdout
