"""CLI: fightmatch scrape | build-dataset | features | recommend."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from fightmatch.config import MatchConfig, ScrapeConfig, normalize_division
from fightmatch.scrape.store import build_dataset
from fightmatch.match.features import build_features
from fightmatch.match import rank_by_division, select_matchups, explain_matchup, load_features_csv
from fightmatch.scrape import scrape_since
from fightmatch.utils.log import log


def _parse_since(s: str) -> str:
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    raise ValueError("--since must be YYYY-MM-DD")


def _division_slug(label: str) -> str:
    """Slug for filenames from a division label (e.g. 'Welterweight' -> 'welterweight')."""
    norm = normalize_division(label) or label.strip().lower()
    slug = norm.replace(" ", "-").replace("/", "-")
    return slug or "all"


def _detect_divisions(processed_dir: Path, features_path: Path | None = None) -> list[tuple[str, str]]:
    """
    Detect divisions from features CSV if available, otherwise from processed bouts.json.
    Returns list of (normalized_key, display_label), sorted by display label.
    """
    divisions: dict[str, str] = {}
    # Prefer features.csv if present (reflects actual feature rows)
    if features_path is not None and features_path.exists():
        try:
            rows = load_features_csv(features_path)
        except Exception:
            rows = []
        for r in rows:
            wc = r.get("weight_class")
            norm = normalize_division(wc)
            if not norm:
                continue
            if norm not in divisions:
                divisions[norm] = wc or norm.title()
    # Fallback to processed bouts.json
    if not divisions:
        bouts_path = processed_dir / "bouts.json"
        if bouts_path.exists():
            try:
                bouts = json.loads(bouts_path.read_text(encoding="utf-8"))
            except Exception:
                bouts = []
            for b in bouts:
                wc = b.get("weight_class")
                norm = normalize_division(wc)
                if not norm:
                    continue
                if norm not in divisions:
                    divisions[norm] = wc or norm.title()
    items = sorted(divisions.items(), key=lambda kv: kv[1].lower())
    return items


def _load_recent_pairs(processed_dir: Path) -> set[tuple[str, str]]:
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
    return recent_pairs


def _write_division_markdown(
    md_path: Path,
    division: str,
    top_contenders: list[dict],
    matchup_recommendations: list[dict],
) -> None:
    """Compact, human-readable division report."""
    ts = datetime.now().isoformat(timespec="seconds")
    with md_path.open("w", encoding="utf-8") as f_md:
        f_md.write("# FightMatch division report\n\n")
        f_md.write(f"**Division:** {division or 'All'}  \n")
        f_md.write(f"**Generated:** {ts}\n\n")

        f_md.write("### How to interpret this report\n")
        f_md.write(
            "- Top contenders are ordered by a composite rank score (recent results, opponent quality, activity, finishes).\n"
        )
        f_md.write(
            "- Recommended matchups prefer competitive fights between active contenders while avoiding immediate rematches and huge rank gaps.\n"
        )
        f_md.write(
            "- Style notes (striking vs grappling, vulnerabilities) are heuristics to highlight \"style test\" matchups.\n\n"
        )

        f_md.write("### Top contenders\n\n")
        for c in top_contenders:
            name = c.get("name") or c.get("fighter_id") or ""
            score = float(c.get("score", 0.0))
            f_md.write(f"{c.get('rank')}. {name} ({score:.3f})\n")

        f_md.write("\n### Top 5 matchup recommendations\n")
        for i, rec in enumerate(matchup_recommendations[:5], start=1):
            f_md.write(f"\n#### {i}. {rec['matchup']}\n")  # type: ignore[index]
            score_a = float(rec.get("score_a", 0.0))  # type: ignore[index]
            score_b = float(rec.get("score_b", 0.0))  # type: ignore[index]
            f_md.write(f"Scores: {score_a:.3f} vs {score_b:.3f}\n")
            expl = rec.get("explanations") or []
            for reason in expl[:4]:
                f_md.write(f"- {reason}\n")


def cmd_scrape(args: argparse.Namespace) -> int:
    out = Path(args.out)
    since = _parse_since(args.since)
    division = (args.division or "").strip()
    log(f"Scraping UFCStats since {since} -> {out}" + (f" (division={division})" if division else ""))
    scrape_since(since, out, config=ScrapeConfig(), division=division)
    return 0


def cmd_build_dataset(args: argparse.Namespace) -> int:
    raw = Path(args.raw)
    out = Path(args.out)
    if not raw.exists():
        log(f"Raw dir not found: {raw}")
        return 1
    division = (args.division or "").strip()
    log(f"Building dataset from {raw} -> {out}" + (f" (division={division})" if division else ""))
    build_dataset(raw, out, division=division)
    bouts_path = out / "bouts.json"
    try:
        bouts = json.loads(bouts_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        log(f"No bouts.json written in {out}. Did you run 'fightmatch scrape' first?")
        return 1
    div_label = division or "All"
    log(f"Dataset complete for division={div_label}: bouts={len(bouts)} (see {bouts_path})")
    if division and not bouts:
        log(f"No bouts found for division={division}. Try a different --since or relax --division.")
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
    log(f"Building features from {inp} -> {out}" + (f" (division={division})" if division else ""))
    build_features(inp, out, division=division)
    # Optionally log how many rows we produced by reusing the loader
    try:
        rows = load_features_csv(out)
        log(f"Features complete: rows={len(rows)} (division={division or 'All'}) -> {out}")
    except Exception:
        log(f"Features written to {out}, but could not re-read CSV for row count")
    log("Wrote features.csv")
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    features_path = Path(args.features)
    processed_dir = Path(args.processed)
    if not features_path.exists():
        log(
            f"Features file not found: {features_path}. "
            f"Run: fightmatch features --in {processed_dir} --out {features_path} --division \"{args.division or 'Welterweight'}\""
        )
        return 1
    config = MatchConfig(
        prioritize_contender_clarity=args.prioritize_contender_clarity,
        prioritize_action=args.prioritize_action,
        allow_short_notice=args.allow_short_notice,
        avoid_immediate_rematch=args.avoid_rematch,
    )
    division = args.division or ""
    ranked = rank_by_division(
        features_path,
        division=division,
        config=config,
        top_n=max(20, args.top * 2),
    )
    if not ranked:
        # Distinguish between "no features at all" and "features exist but not for this division"
        try:
            all_rows = load_features_csv(features_path)
        except Exception:
            all_rows = []
        if not all_rows:
            log(
                f"No feature rows found in {features_path}. "
                f"Run: fightmatch features --in {processed_dir} --out {features_path} --division \"{division or 'Welterweight'}\""
            )
        else:
            log(
                f"No fighters found in division={division or 'All'} within features. "
                f"Re-run: fightmatch features --division \"{division or 'Welterweight'}\" after scrape + build-dataset."
            )
        return 1
    # Recent pairs from bouts
    recent_pairs = _load_recent_pairs(processed_dir)
    matchups = select_matchups(
        ranked,
        top_n=args.top,
        config=config,
        recent_pairs=recent_pairs,
    )
    id_to_pos: dict[str, int] = {}
    for idx, (row, _) in enumerate(ranked, start=1):
        id_to_pos[row.get("fighter_id", "")] = idx

    log(
        f"Recommend: contenders={len(ranked)}, matchups={len(matchups)} "
        f"(division={division or 'All'}) from features={features_path}"
    )

    # Build report payload for JSON
    top_contenders = [
        {"rank": i, "fighter_id": row.get("fighter_id"), "name": row.get("name"), "score": float(score)}
        for i, (row, score) in enumerate(ranked[:10], start=1)
    ]
    matchup_recommendations = []
    for i, (fa, fb, ra, rb) in enumerate(matchups[:5], start=1):
        id_a = fa.get("fighter_id", "")
        id_b = fb.get("fighter_id", "")
        pos_a = id_to_pos.get(id_a)
        pos_b = id_to_pos.get(id_b)
        rank_pos = (pos_a, pos_b) if pos_a and pos_b else None
        reasons = explain_matchup(fa, fb, ra, rb, rank_positions=rank_pos)
        matchup_recommendations.append({
            "matchup": f"{fa.get('name', id_a)} vs {fb.get('name', id_b)}",
            "fighter_a_id": id_a,
            "fighter_b_id": id_b,
            "score_a": round(float(ra), 3),
            "score_b": round(float(rb), 3),
            "explanations": reasons,
        })
    reports_dir = Path(args.reports_dir or "data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "recommend.json"
    report_data = {
        "division": division or "All",
        "top_contenders": top_contenders,
        "matchup_recommendations": matchup_recommendations,
    }
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    log(f"Wrote {report_path}")

    # Also emit a short Markdown report alongside the JSON artifact
    md_path = reports_dir / "recommend.md"
    _write_division_markdown(md_path, division or "All", top_contenders, matchup_recommendations)
    log(f"Wrote {md_path}")
def cmd_divisions(args: argparse.Namespace) -> int:
    processed = Path(args.processed)
    features_path = Path(args.features) if args.features else None
    divisions = _detect_divisions(processed, features_path)
    if not divisions:
        log(
            f"No divisions detected. Run: fightmatch scrape --since YYYY-MM-DD --out data/raw "
            f"and fightmatch build-dataset --raw data/raw --out {processed}"
        )
        return 1
    print("# FightMatch divisions")
    for _, label in divisions:
        print(label)
    return 0


def cmd_recommend_all(args: argparse.Namespace) -> int:
    features_path = Path(args.features)
    processed_dir = Path(args.processed)
    reports_dir = Path(args.reports_dir or "data/reports")
    if not features_path.exists():
        log(
            f"Features file not found: {features_path}. "
            f"Run: fightmatch features --in {processed_dir} --out {features_path}"
        )
        return 1
    divisions = _detect_divisions(processed_dir, features_path)
    if not divisions:
        log(
            "No divisions detected in data. Run: fightmatch scrape ... && "
            "fightmatch build-dataset ... && fightmatch features ..."
        )
        return 1

    config = MatchConfig(
        prioritize_contender_clarity=args.prioritize_contender_clarity,
        prioritize_action=args.prioritize_action,
        allow_short_notice=args.allow_short_notice,
        avoid_immediate_rematch=args.avoid_rematch,
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    recent_pairs = _load_recent_pairs(processed_dir)

    summary_entries: list[dict] = []

    for norm, label in divisions:
        division = label
        ranked = rank_by_division(
            features_path,
            division=division,
            config=config,
            top_n=max(20, args.top * 2),
        )
        if not ranked:
            log(f"Skipping division={division}: no fighters with features.")
            continue
        matchups = select_matchups(
            ranked,
            top_n=args.top,
            config=config,
            recent_pairs=recent_pairs,
        )
        if not matchups:
            log(f"Skipping division={division}: could not form matchups given constraints.")
            continue

        id_to_pos: dict[str, int] = {}
        for idx, (row, _) in enumerate(ranked, start=1):
            id_to_pos[row.get("fighter_id", "")] = idx

        top_contenders = [
            {"rank": i, "fighter_id": row.get("fighter_id"), "name": row.get("name"), "score": float(score)}
            for i, (row, score) in enumerate(ranked[:10], start=1)
        ]
        matchup_recommendations = []
        for i, (fa, fb, ra, rb) in enumerate(matchups[:5], start=1):
            id_a = fa.get("fighter_id", "")
            id_b = fb.get("fighter_id", "")
            pos_a = id_to_pos.get(id_a)
            pos_b = id_to_pos.get(id_b)
            rank_pos = (pos_a, pos_b) if pos_a and pos_b else None
            reasons = explain_matchup(fa, fb, ra, rb, rank_positions=rank_pos)
            matchup_recommendations.append({
                "matchup": f"{fa.get('name', id_a)} vs {fb.get('name', id_b)}",
                "fighter_a_id": id_a,
                "fighter_b_id": id_b,
                "score_a": round(float(ra), 3),
                "score_b": round(float(rb), 3),
                "explanations": reasons,
            })

        slug = _division_slug(division)
        json_path = reports_dir / f"{slug}.json"
        md_path = reports_dir / f"{slug}.md"
        report_data = {
            "division": division,
            "top_contenders": top_contenders,
            "matchup_recommendations": matchup_recommendations,
        }
        json_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")

        _write_division_markdown(md_path, division, top_contenders, matchup_recommendations)

        log(f"Wrote {json_path}")
        log(f"Wrote {md_path}")

        summary_entries.append(
            {
                "division": division,
                "top_contenders": top_contenders[:3],
                "top_matchup": matchup_recommendations[0] if matchup_recommendations else None,
            }
        )

    # Summary across divisions
    if summary_entries:
        summary_path = reports_dir / "summary.md"
        with summary_path.open("w", encoding="utf-8") as f_md:
            ts = datetime.now().isoformat(timespec="seconds")
            f_md.write("# FightMatch summary\n\n")
            f_md.write(f"**Generated:** {ts}\n\n")
            f_md.write("## Divisions\n")
            for entry in summary_entries:
                f_md.write(f"- {entry['division']}\n")
            for entry in summary_entries:
                f_md.write(f"\n## {entry['division']}\n")
                f_md.write("Top 3 contenders:\n")
                for c in entry["top_contenders"]:
                    name = c.get("name") or c.get("fighter_id") or ""
                    score = float(c.get("score", 0.0))
                    f_md.write(f"- {c.get('rank')}. {name} ({score:.3f})\n")
                top_matchup = entry.get("top_matchup")
                if top_matchup:
                    f_md.write("\nTop matchup:\n")
                    score_a = float(top_matchup.get("score_a", 0.0))
                    score_b = float(top_matchup.get("score_b", 0.0))
                    f_md.write(
                        f"- {top_matchup['matchup']} ({score_a:.3f} vs {score_b:.3f})\n"  # type: ignore[index]
                    )
        log(f"Wrote {summary_path}")
        return 0

    log("No divisions produced matchups; nothing to recommend.")
    return 1


def cmd_demo(args: argparse.Namespace) -> int:
    """
    Lightweight local demo:
    - Assumes data has already been scraped + processed + features built.
    - Runs recommend-all across all detected divisions.
    """
    processed_dir = Path(args.processed)
    features_path = Path(args.features)
    reports_dir = Path(args.reports_dir or "data/reports")

    if not processed_dir.exists() or not (processed_dir / "bouts.json").exists():
        log(
            f"No processed data found in {processed_dir}. "
            "Run: fightmatch scrape --since YYYY-MM-DD --out data/raw "
            f"and fightmatch build-dataset --raw data/raw --out {processed_dir}"
        )
        return 1
    if not features_path.exists():
        log(
            f"No features file found at {features_path}. "
            f"Run: fightmatch features --in {processed_dir} --out {features_path}"
        )
        return 1

    log("Running FightMatch demo: recommend-all across detected divisions.")
    demo_args = argparse.Namespace(
        top=args.top,
        features=str(features_path),
        processed=str(processed_dir),
        reports_dir=str(reports_dir),
        prioritize_contender_clarity=True,
        prioritize_action=args.prioritize_action,
        allow_short_notice=False,
        avoid_rematch=True,
    )
    rc = cmd_recommend_all(demo_args)
    if rc == 0:
        log(f"Demo complete. Reports written under {reports_dir}")
    return rc


    # Compact terminal summary: top 10 + 5 matchups
    print("# FightMatch recommended matchups")
    print(f"# Division: {division or 'All'}")
    print()
    print("## Top 10 contenders")
    for i, (row, score) in enumerate(ranked[:10], start=1):
        print(f"  {i}. {row.get('name', row.get('fighter_id', ''))} ({score:.3f})")
    print()
    print("## Suggested matchups (5)")
    for i, (fa, fb, ra, rb) in enumerate(matchups[:5], start=1):
        id_a = fa.get("fighter_id", "")
        id_b = fb.get("fighter_id", "")
        pos_a = id_to_pos.get(id_a)
        pos_b = id_to_pos.get(id_b)
        rank_pos = (pos_a, pos_b) if pos_a and pos_b else None
        reasons = explain_matchup(fa, fb, ra, rb, rank_positions=rank_pos)
        print(f"  {i}. {fa.get('name', id_a)} vs {fb.get('name', id_b)}")
        print(f"     Scores: {ra:.3f} vs {rb:.3f}")
        for r in reasons[:3]:
            print(f"     - {r}")
        print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="fightmatch", description="UFC matchmaking + rankings decision support")
    sub = parser.add_subparsers(dest="cmd", required=True)
    # scrape
    p_scrape = sub.add_parser("scrape", help="Scrape UFCStats since date")
    p_scrape.add_argument("--since", default="2020-01-01", help="YYYY-MM-DD")
    p_scrape.add_argument("--out", default="data/raw", help="Raw output dir")
    p_scrape.add_argument("--division", default="", help="Optional weight class; only download fight pages for this division")
    p_scrape.set_defaults(func=cmd_scrape)
    # build-dataset
    p_build = sub.add_parser("build-dataset", help="Parse raw HTML into JSON/JSONL")
    p_build.add_argument("--raw", default="data/raw", help="Raw dir")
    p_build.add_argument("--out", default="data/processed", help="Processed output dir")
    p_build.add_argument("--division", default="", help="Optional weight class; only emit bouts/stats for this division")
    p_build.set_defaults(func=cmd_build_dataset)
    # features
    p_feat = sub.add_parser("features", help="Build per-fighter features CSV")
    p_feat.add_argument("--in", dest="inp", default="data/processed", help="Processed dir")
    p_feat.add_argument("--out", default="data/features/features.csv", help="Output CSV path")
    p_feat.add_argument("--division", default="", help="Optional weight class; only output rows for this division")
    p_feat.set_defaults(func=cmd_features)
    # recommend
    p_rec = sub.add_parser("recommend", help="Print recommended matchups with explanations")
    p_rec.add_argument("--division", default="", help="Weight class (e.g. Lightweight)")
    p_rec.add_argument("--top", type=int, default=10, help="Number of matchups")
    p_rec.add_argument("--features", default="data/features/features.csv", help="Features CSV")
    p_rec.add_argument("--processed", default="data/processed", help="Processed dir (for recent bouts)")
    p_rec.add_argument("--reports-dir", default="data/reports", help="Write recommend JSON here")
    p_rec.add_argument("--prioritize-contender-clarity", action="store_true", default=True, dest="prioritize_contender_clarity")
    p_rec.add_argument("--no-prioritize-contender-clarity", action="store_false", dest="prioritize_contender_clarity")
    p_rec.add_argument("--prioritize-action", action="store_true", default=False, dest="prioritize_action")
    p_rec.add_argument("--allow-short-notice", action="store_true", default=False, dest="allow_short_notice")
    p_rec.add_argument("--avoid-rematch", action="store_true", default=True, dest="avoid_rematch")
    p_rec.add_argument("--no-avoid-rematch", action="store_false", dest="avoid_rematch")
    p_rec.set_defaults(func=cmd_recommend)
    # divisions
    p_div = sub.add_parser("divisions", help="List detected divisions from processed data/features")
    p_div.add_argument("--processed", default="data/processed", help="Processed dir")
    p_div.add_argument("--features", default="data/features/features.csv", help="Features CSV (optional)")
    p_div.set_defaults(func=cmd_divisions)
    # recommend-all
    p_rec_all = sub.add_parser("recommend-all", help="Recommend matchups for all detected divisions")
    p_rec_all.add_argument("--top", type=int, default=5, help="Number of matchups per division")
    p_rec_all.add_argument("--features", default="data/features/features.csv", help="Features CSV")
    p_rec_all.add_argument("--processed", default="data/processed", help="Processed dir (for recent bouts)")
    p_rec_all.add_argument("--reports-dir", default="data/reports", help="Write division reports + summary here")
    p_rec_all.add_argument("--prioritize-contender-clarity", action="store_true", default=True, dest="prioritize_contender_clarity")
    p_rec_all.add_argument("--no-prioritize-contender-clarity", action="store_false", dest="prioritize_contender_clarity")
    p_rec_all.add_argument("--prioritize-action", action="store_true", default=False, dest="prioritize_action")
    p_rec_all.add_argument("--allow-short-notice", action="store_true", default=False, dest="allow_short_notice")
    p_rec_all.add_argument("--avoid-rematch", action="store_true", default=True, dest="avoid_rematch")
    p_rec_all.add_argument("--no-avoid-rematch", action="store_false", dest="avoid_rematch")
    p_rec_all.set_defaults(func=cmd_recommend_all)
    # demo
    p_demo = sub.add_parser("demo", help="Run a local FightMatch demo (no scraping).")
    p_demo.add_argument("--top", type=int, default=5, help="Number of matchups per division")
    p_demo.add_argument("--processed", default="data/processed", help="Processed dir")
    p_demo.add_argument("--features", default="data/features/features.csv", help="Features CSV")
    p_demo.add_argument("--reports-dir", default="data/reports", help="Write reports + summary here")
    p_demo.add_argument("--prioritize-action", action="store_true", default=False, dest="prioritize_action")
    p_demo.set_defaults(func=cmd_demo)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
