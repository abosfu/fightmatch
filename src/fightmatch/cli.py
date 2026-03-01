"""CLI: fightmatch scrape | build-dataset | features | recommend."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fightmatch.config import MatchConfig, ScrapeConfig, get_cache_dir, get_features_dir, get_processed_dir
from fightmatch.data import build_dataset, build_features
from fightmatch.match import rank_by_division, select_matchups, explain_matchup
from fightmatch.scrape import scrape_since
from fightmatch.utils.log import log


def _parse_since(s: str) -> str:
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    raise ValueError("--since must be YYYY-MM-DD")


def cmd_scrape(args: argparse.Namespace) -> int:
    out = Path(args.out)
    since = _parse_since(args.since)
    log(f"Scraping UFCStats since {since} -> {out}")
    scrape_since(since, out, config=ScrapeConfig())
    return 0


def cmd_build_dataset(args: argparse.Namespace) -> int:
    raw = Path(args.raw)
    out = Path(args.out)
    if not raw.exists():
        log(f"Raw dir not found: {raw}")
        return 1
    log(f"Building dataset from {raw} -> {out}")
    build_dataset(raw, out)
    log("Wrote fighters.json, events.json, bouts.json, stats.jsonl")
    return 0


def cmd_features(args: argparse.Namespace) -> int:
    inp = Path(args.inp)
    out = Path(args.out)
    if not inp.exists():
        log(f"Processed dir not found: {inp}")
        return 1
    log(f"Building features from {inp} -> {out}")
    build_features(inp, out)
    log("Wrote features.csv")
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    features_path = Path(args.features)
    processed_dir = Path(args.processed)
    if not features_path.exists():
        log(f"Features file not found: {features_path}. Run: fightmatch features --in data/processed --out data/features/features.csv")
        return 1
    config = MatchConfig(
        prioritize_contender_clarity=args.prioritize_contender_clarity,
        prioritize_action=args.prioritize_action,
        allow_short_notice=args.allow_short_notice,
        avoid_immediate_rematch=args.avoid_rematch,
    )
    ranked = rank_by_division(
        features_path,
        division=args.division or "",
        config=config,
        top_n=max(20, args.top * 2),
    )
    if not ranked:
        log("No fighters in division (or no features). Run scrape + build-dataset + features first.")
        return 1
    # Recent pairs from bouts
    recent_pairs: set[tuple[str, str]] = set()
    bouts_path = processed_dir / "bouts.json"
    if processed_dir.exists() and bouts_path.exists():
        try:
            bouts = json.loads(bouts_path.read_text(encoding="utf-8"))
            for b in bouts:
                r = b.get("red_fighter_id")
                bl = b.get("blue_fighter_id")
                if r and bl:
                    recent_pairs.add((min(r, bl), max(r, bl)))
        except Exception:
            pass
    matchups = select_matchups(
        ranked,
        top_n=args.top,
        config=config,
        recent_pairs=recent_pairs,
    )
    # Rank positions for explanation
    id_to_pos: dict[str, int] = {}
    for idx, (row, _) in enumerate(ranked, start=1):
        id_to_pos[row.get("fighter_id", "")] = idx
    print("# FightMatch recommended matchups")
    print(f"# Division: {args.division or 'All'}")
    print()
    for i, (fa, fb, ra, rb) in enumerate(matchups, start=1):
        id_a = fa.get("fighter_id", "")
        id_b = fb.get("fighter_id", "")
        pos_a = id_to_pos.get(id_a)
        pos_b = id_to_pos.get(id_b)
        rank_pos = (pos_a, pos_b) if pos_a and pos_b else None
        reasons = explain_matchup(fa, fb, ra, rb, rank_positions=rank_pos)
        print(f"## {i}. {fa.get('name', id_a)} vs {fb.get('name', id_b)}")
        print(f"   Rank scores: {ra:.3f} vs {rb:.3f}")
        for r in reasons:
            print(f"   - {r}")
        print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="fightmatch", description="UFC matchmaking + rankings decision support")
    sub = parser.add_subparsers(dest="cmd", required=True)
    # scrape
    p_scrape = sub.add_parser("scrape", help="Scrape UFCStats since date")
    p_scrape.add_argument("--since", default="2020-01-01", help="YYYY-MM-DD")
    p_scrape.add_argument("--out", default="data/raw", help="Raw output dir")
    p_scrape.set_defaults(func=cmd_scrape)
    # build-dataset
    p_build = sub.add_parser("build-dataset", help="Parse raw HTML into JSON/JSONL")
    p_build.add_argument("--raw", default="data/raw", help="Raw dir")
    p_build.add_argument("--out", default="data/processed", help="Processed output dir")
    p_build.set_defaults(func=cmd_build_dataset)
    # features
    p_feat = sub.add_parser("features", help="Build per-fighter features CSV")
    p_feat.add_argument("--in", dest="inp", default="data/processed", help="Processed dir")
    p_feat.add_argument("--out", default="data/features/features.csv", help="Output CSV path")
    p_feat.set_defaults(func=cmd_features)
    # recommend
    p_rec = sub.add_parser("recommend", help="Print recommended matchups with explanations")
    p_rec.add_argument("--division", default="", help="Weight class (e.g. Lightweight)")
    p_rec.add_argument("--top", type=int, default=10, help="Number of matchups")
    p_rec.add_argument("--features", default="data/features/features.csv", help="Features CSV")
    p_rec.add_argument("--processed", default="data/processed", help="Processed dir (for recent bouts)")
    p_rec.add_argument("--prioritize-contender-clarity", action="store_true", default=True, dest="prioritize_contender_clarity")
    p_rec.add_argument("--no-prioritize-contender-clarity", action="store_false", dest="prioritize_contender_clarity")
    p_rec.add_argument("--prioritize-action", action="store_true", default=False, dest="prioritize_action")
    p_rec.add_argument("--allow-short-notice", action="store_true", default=False, dest="allow_short_notice")
    p_rec.add_argument("--avoid-rematch", action="store_true", default=True, dest="avoid_rematch")
    p_rec.add_argument("--no-avoid-rematch", action="store_false", dest="avoid_rematch")
    p_rec.set_defaults(func=cmd_recommend)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
