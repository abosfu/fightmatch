"""CLI commands: scrape, build-dataset, features."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

from fightmatch.config import ScrapeConfig
from fightmatch.match import load_features_csv
from fightmatch.match.features import build_features
from fightmatch.scrape import scrape_since
from fightmatch.scrape.store import build_dataset
from fightmatch.utils.log import log

from ._util import parse_since


def cmd_scrape(args: argparse.Namespace) -> int:
    out = Path(args.out)
    since = parse_since(args.since)
    division = (args.division or "").strip()
    log(
        f"Scraping UFCStats since {since} -> {out}"
        + (f" (division={division})" if division else "")
    )
    try:
        scrape_since(since, out, config=ScrapeConfig(), division=division)
        return 0
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        log(f"Network error: could not reach UFCStats ({type(e).__name__}).")
        _suggest_offline_path(out)
        return 1
    except requests.exceptions.RequestException as e:
        log(f"UFCStats request failed: {e}")
        _suggest_offline_path(out)
        return 1
    except Exception as e:
        log(f"Scrape failed: {e}")
        _suggest_offline_path(out)
        return 1


def _suggest_offline_path(raw_dir: Path) -> None:
    cached_events = (
        list((raw_dir / "ufcstats" / "events").glob("*.html"))
        if raw_dir.exists()
        else []
    )
    if cached_events:
        log(
            f"Cached HTML found in {raw_dir} ({len(cached_events)} event file(s)). "
            "You can continue with cached data:"
        )
        log(f"  fightmatch build-dataset --raw {raw_dir} --out data/processed")
        log(
            "  fightmatch features --in data/processed --out data/features/features.csv"
        )
        log(
            "  fightmatch demo --processed data/processed --features data/features/features.csv"
        )
    else:
        log("No cached data found. UFCStats must be reachable to build a dataset.")
        log("Retry when the connection is restored:")
        log(f"  fightmatch scrape --since YYYY-MM-DD --out {raw_dir}")


def cmd_build_dataset(args: argparse.Namespace) -> int:
    raw = Path(args.raw)
    out = Path(args.out)
    if not raw.exists():
        log(f"Raw dir not found: {raw}")
        return 1
    division = (args.division or "").strip()
    log(
        f"Building dataset from {raw} -> {out}"
        + (f" (division={division})" if division else "")
    )
    build_dataset(raw, out, division=division)
    bouts_path = out / "bouts.json"
    try:
        bouts = json.loads(bouts_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        log(f"No bouts.json written in {out}. Did you run 'fightmatch scrape' first?")
        return 1
    div_label = division or "All"
    log(
        f"Dataset complete for division={div_label}: bouts={len(bouts)} (see {bouts_path})"
    )
    if division and not bouts:
        log(
            f"No bouts found for division={division}. Try a different --since or relax --division."
        )
        return 1
    log("Wrote fighters.json, events.json, bouts.json, stats.jsonl")
    return 0


def cmd_features(args: argparse.Namespace) -> int:
    inp = Path(args.inp)
    out = Path(args.out)
    if not inp.exists():
        log(f"Processed dir not found: {inp}")
        return 1
    division = (args.division or "").strip()
    log(
        f"Building features from {inp} -> {out}"
        + (f" (division={division})" if division else "")
    )
    build_features(inp, out, division=division)
    try:
        rows = load_features_csv(out)
        log(
            f"Features complete: rows={len(rows)} (division={division or 'All'}) -> {out}"
        )
    except Exception:
        log(f"Features written to {out}, but could not re-read CSV for row count")
    log("Wrote features.csv")
    return 0
