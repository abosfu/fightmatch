"""CLI smoke tests: welterweight pipeline with fixtures (no network)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest


def _run_fightmatch(*args: str, cwd: Optional[str] = None, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """Run fightmatch CLI via same Python as test runner."""
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
    """Raw dir with fixture HTML: event has Welterweight bout1, Lightweight bout2; only bout1 has fight details."""
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


def test_cli_build_dataset_welterweight_only(raw_dir_from_fixtures: Path, tmp_path: Path) -> None:
    """build-dataset --division Welterweight emits only welterweight bout and its stats."""
    out = tmp_path / "processed"
    proc = _run_fightmatch(
        "build-dataset",
        "--raw", str(raw_dir_from_fixtures),
        "--out", str(out),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert (out / "fighters.json").exists()
    assert (out / "events.json").exists()
    assert (out / "bouts.json").exists()
    assert (out / "stats.jsonl").exists()
    bouts = json.loads((out / "bouts.json").read_text())
    assert len(bouts) == 1
    assert bouts[0].get("weight_class") == "Welterweight"
    assert bouts[0].get("bout_id") == "bout1"
    fighters = json.loads((out / "fighters.json").read_text())
    assert len(fighters) >= 2


def test_cli_features_welterweight_only(raw_dir_from_fixtures: Path, tmp_path: Path) -> None:
    """features --division Welterweight outputs only welterweight rows."""
    processed = tmp_path / "processed"
    proc = _run_fightmatch(
        "build-dataset",
        "--raw", str(raw_dir_from_fixtures),
        "--out", str(processed),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0
    out_csv = tmp_path / "features.csv"
    proc = _run_fightmatch(
        "features",
        "--in", str(processed),
        "--out", str(out_csv),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert out_csv.exists()
    text = out_csv.read_text()
    assert "fighter_id" in text
    assert "Welterweight" in text


def test_cli_recommend_fails_when_features_missing(tmp_path: Path) -> None:
    """recommend exits non-zero when features file does not exist."""
    proc = _run_fightmatch(
        "recommend",
        "--features", str(tmp_path / "nonexistent.csv"),
        "--processed", str(tmp_path),
        "--division", "Welterweight",
        "--top", "5",
    )
    assert proc.returncode == 1


def test_cli_recommend_welterweight_writes_report_and_prints_summary(
    raw_dir_from_fixtures: Path, tmp_path: Path
) -> None:
    """Full welterweight pipeline: build-dataset -> features -> recommend; report JSON and terminal summary."""
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    proc = _run_fightmatch(
        "build-dataset",
        "--raw", str(raw_dir_from_fixtures),
        "--out", str(processed),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0
    features_csv = tmp_path / "features.csv"
    proc = _run_fightmatch(
        "features",
        "--in", str(processed),
        "--out", str(features_csv),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0
    proc = _run_fightmatch(
        "recommend",
        "--features", str(features_csv),
        "--processed", str(processed),
        "--division", "Welterweight",
        "--top", "5",
        "--reports-dir", str(reports),
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert (reports / "recommend.json").exists()
    data = json.loads((reports / "recommend.json").read_text())
    assert data.get("division") == "Welterweight"
    assert "top_contenders" in data
    assert "matchup_recommendations" in data


def test_cli_divisions_and_recommend_all(raw_dir_from_fixtures: Path, tmp_path: Path) -> None:
    """divisions lists Welterweight; recommend-all generates per-division reports and summary."""
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    features_csv = tmp_path / "features.csv"

    # Build minimal welterweight processed + features
    proc = _run_fightmatch(
        "build-dataset",
        "--raw", str(raw_dir_from_fixtures),
        "--out", str(processed),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    proc = _run_fightmatch(
        "features",
        "--in", str(processed),
        "--out", str(features_csv),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)

    # divisions
    proc = _run_fightmatch(
        "divisions",
        "--processed", str(processed),
        "--features", str(features_csv),
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "Welterweight" in proc.stdout

    # recommend-all
    proc = _run_fightmatch(
        "recommend-all",
        "--features", str(features_csv),
        "--processed", str(processed),
        "--reports-dir", str(reports),
        "--top", "3",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    # Only welterweight division exists in this fixture-based pipeline
    welter_slug = "welterweight"
    assert (reports / f"{welter_slug}.json").exists()
    assert (reports / f"{welter_slug}.md").exists()
    assert (reports / "summary.md").exists()
    data = json.loads((reports / f"{welter_slug}.json").read_text())
    assert data.get("division") == "Welterweight"
    assert "top_contenders" in data
    assert "matchup_recommendations" in data


def test_cli_demo_uses_existing_data(raw_dir_from_fixtures: Path, tmp_path: Path) -> None:
    """demo reuses processed + features and writes reports/summary without network."""
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    features_csv = tmp_path / "features.csv"

    proc = _run_fightmatch(
        "build-dataset",
        "--raw", str(raw_dir_from_fixtures),
        "--out", str(processed),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    proc = _run_fightmatch(
        "features",
        "--in", str(processed),
        "--out", str(features_csv),
        "--division", "Welterweight",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)

    proc = _run_fightmatch(
        "demo",
        "--processed", str(processed),
        "--features", str(features_csv),
        "--reports-dir", str(reports),
        "--top", "3",
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert (reports / "summary.md").exists()
