"""CLI: fightmatch scrape | build-dataset | features | recommend | fighter-profile | simulate."""

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
from fightmatch.analytics.rating import rate_all
from fightmatch.analytics.profile import (
    build_profile,
    profile_to_dict,
    format_profile_terminal,
    format_profile_markdown,
)
from fightmatch.engine.simulate import (
    simulate,
    simulation_to_dict,
    format_simulation_terminal,
    format_simulation_markdown,
)
from fightmatch.engine.promoter import select_matchups_ranked


# ── Shared utilities ──────────────────────────────────────────────────────────

def _parse_since(s: str) -> str:
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    raise ValueError("--since must be YYYY-MM-DD")


def _division_slug(label: str) -> str:
    norm = normalize_division(label) or label.strip().lower()
    slug = norm.replace(" ", "-").replace("/", "-")
    return slug or "all"


def _detect_divisions(processed_dir: Path, features_path: Path | None = None) -> list[tuple[str, str]]:
    """
    Detect divisions from features CSV if available, otherwise from processed bouts.json.
    Returns list of (normalized_key, display_label) sorted by display label.
    """
    divisions: dict[str, str] = {}
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
    return sorted(divisions.items(), key=lambda kv: kv[1].lower())


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


def _find_fighter_rows(rows: list[dict], name: str) -> list[dict]:
    """Case-insensitive substring search for a fighter by name."""
    needle = name.strip().lower()
    return [r for r in rows if needle in (r.get("name") or "").lower()]


def _write_division_markdown(
    md_path: Path,
    division: str,
    top_contenders: list[dict],
    matchup_recommendations: list[dict],
) -> None:
    """Human-readable division report with promoter scoring when available."""
    ts = datetime.now().isoformat(timespec="seconds")
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# FightMatch division report\n\n")
        f.write(f"**Division:** {division or 'All'}  \n")
        f.write(f"**Generated:** {ts}\n\n")
        f.write("### How to interpret this report\n")
        f.write(
            "- Top contenders are ordered by the FightMatch fighter rating (0–10 scale). "
            "The rating combines activity, form, striking/grappling efficiency, opponent quality, "
            "and finish ability.\n"
        )
        f.write(
            "- Recommended matchups are ordered by promoter score — a weighted combination of "
            "competitive balance, divisional relevance, activity readiness, freshness, style interest, "
            "and fan engagement proxy.\n\n"
        )

        f.write("### Top contenders\n\n")
        for c in top_contenders:
            name = c.get("name") or c.get("fighter_id") or ""
            score = float(c.get("score", 0.0))
            f.write(f"{c.get('rank')}. {name} ({score:.2f})\n")

        f.write("\n### Top 5 matchup recommendations\n")
        for i, rec in enumerate(matchup_recommendations[:5], start=1):
            f.write(f"\n#### {i}. {rec['matchup']}\n")
            score_a = float(rec.get("score_a", 0.0))
            score_b = float(rec.get("score_b", 0.0))
            f.write(f"Ratings: {score_a:.2f} vs {score_b:.2f}")
            if "promoter_score" in rec:
                f.write(f"  |  Promoter score: {rec['promoter_score']:.3f} ({rec.get('promoter_tier', '')})")
            f.write("\n")
            if "win_prob_a" in rec:
                f.write(f"Win probability: {rec['win_prob_a']:.0%} / {rec['win_prob_b']:.0%}  ")
                f.write(f"  Competitiveness: {rec.get('competitiveness', 0):.2f}")
                f.write(f"  |  Style contrast: {rec.get('style_contrast', 0):.2f}\n")
            expl = rec.get("explanations") or []
            for reason in expl[:4]:
                f.write(f"- {reason}\n")


# ── Command implementations ───────────────────────────────────────────────────

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
    try:
        rows = load_features_csv(out)
        log(f"Features complete: rows={len(rows)} (division={division or 'All'}) -> {out}")
    except Exception:
        log(f"Features written to {out}, but could not re-read CSV for row count")
    log("Wrote features.csv")
    return 0


def cmd_fighter_profile(args: argparse.Namespace) -> int:
    """Build and display a comprehensive analytics profile for a fighter."""
    features_path = Path(args.features)
    if not features_path.exists():
        log(f"Features file not found: {features_path}")
        return 1

    all_rows = load_features_csv(features_path)
    matches = _find_fighter_rows(all_rows, args.fighter)

    if not matches:
        log(f"No fighter found matching: '{args.fighter}'")
        log(f"Available fighters: {', '.join(r.get('name', '') for r in all_rows[:10])}")
        return 1

    reports_dir = Path(args.reports_dir or "data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    for row in matches:
        # Get all fighters in the same division for percentile calculation
        division = row.get("weight_class", "")
        norm = normalize_division(division)
        division_rows = [
            r for r in all_rows
            if normalize_division(r.get("weight_class")) == norm
        ] if norm else all_rows

        profile = build_profile(row, division_rows)

        # Terminal output
        print(format_profile_terminal(profile))

        # JSON report
        fighter_slug = (row.get("name") or row.get("fighter_id", "unknown")).lower().replace(" ", "_")
        json_path = reports_dir / f"fighter_profile_{fighter_slug}.json"
        json_path.write_text(json.dumps(profile_to_dict(profile), indent=2), encoding="utf-8")
        log(f"Wrote {json_path}")

        # Markdown report
        md_path = reports_dir / f"fighter_profile_{fighter_slug}.md"
        md_path.write_text(format_profile_markdown(profile), encoding="utf-8")
        log(f"Wrote {md_path}")

    if len(matches) > 1:
        log(f"Found {len(matches)} fighters matching '{args.fighter}'. Use a more specific name to narrow down.")

    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    """Run a matchup simulation between two named fighters."""
    features_path = Path(args.features)
    if not features_path.exists():
        log(f"Features file not found: {features_path}")
        return 1

    all_rows = load_features_csv(features_path)

    matches_a = _find_fighter_rows(all_rows, args.fighter_a)
    matches_b = _find_fighter_rows(all_rows, args.fighter_b)

    if not matches_a:
        log(f"Fighter not found: '{args.fighter_a}'")
        return 1
    if not matches_b:
        log(f"Fighter not found: '{args.fighter_b}'")
        return 1

    row_a = matches_a[0]
    row_b = matches_b[0]

    if row_a.get("fighter_id") == row_b.get("fighter_id"):
        log("Both names resolved to the same fighter. Use more specific names.")
        return 1

    # Compute rank positions within shared division
    division_a = normalize_division(row_a.get("weight_class", ""))
    division_b = normalize_division(row_b.get("weight_class", ""))
    if division_a and division_b and division_a == division_b:
        division_rows = [r for r in all_rows if normalize_division(r.get("weight_class")) == division_a]
    else:
        division_rows = all_rows

    ratings = rate_all(division_rows)
    ratings_sorted = sorted(ratings, key=lambda r: -r.rating)
    id_to_rank = {r.fighter_id: i + 1 for i, r in enumerate(ratings_sorted)}

    rank_a = id_to_rank.get(row_a.get("fighter_id", ""))
    rank_b = id_to_rank.get(row_b.get("fighter_id", ""))
    n_fighters = len(division_rows)

    sim = simulate(row_a, row_b, rank_pos_a=rank_a, rank_pos_b=rank_b, n_division_fighters=n_fighters)

    # Terminal output
    print(format_simulation_terminal(sim))

    # Write reports
    reports_dir = Path(args.reports_dir or "data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / "simulate.json"
    json_path.write_text(json.dumps(simulation_to_dict(sim), indent=2), encoding="utf-8")
    log(f"Wrote {json_path}")

    md_path = reports_dir / "simulate.md"
    md_path.write_text(format_simulation_markdown(sim), encoding="utf-8")
    log(f"Wrote {md_path}")

    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    features_path = Path(args.features)
    processed_dir = Path(args.processed)

    if not features_path.exists():
        log(
            f"Features file not found: {features_path}. "
            f"Run: fightmatch features --in {processed_dir} --out {features_path} "
            f"--division \"{args.division or 'Welterweight'}\""
        )
        return 1

    config = MatchConfig(
        prioritize_contender_clarity=args.prioritize_contender_clarity,
        prioritize_action=args.prioritize_action,
        allow_short_notice=args.allow_short_notice,
        avoid_immediate_rematch=args.avoid_rematch,
    )
    division = args.division or ""

    # Load and filter rows for this division
    all_rows = load_features_csv(features_path)
    target = normalize_division(division)
    if target:
        div_rows = [r for r in all_rows if normalize_division(r.get("weight_class")) == target]
    else:
        div_rows = all_rows

    if not div_rows:
        if not all_rows:
            log(
                f"No feature rows found in {features_path}. "
                f"Run: fightmatch features --in {processed_dir} --out {features_path} "
                f"--division \"{division or 'Welterweight'}\""
            )
        else:
            log(
                f"No fighters found for division={division or 'All'} in {features_path}."
            )
        return 1

    # Rate and rank fighters
    ratings = rate_all(div_rows)
    rated = sorted(zip(div_rows, ratings), key=lambda x: -x[1].rating)
    top_n_candidates = min(max(20, args.top * 2), len(rated))
    candidates = [(row, r.rating) for row, r in rated[:top_n_candidates]]

    recent_pairs = _load_recent_pairs(processed_dir)

    # Select matchups using promoter decision scoring
    selected = select_matchups_ranked(
        candidates,
        top_n=args.top,
        recent_pairs=recent_pairs,
        allow_short_notice=config.allow_short_notice,
    )

    if not selected:
        log(f"Could not form matchups for division={division or 'All'} given current constraints.")
        return 1

    log(
        f"Recommend: contenders={len(candidates)}, matchups={len(selected)} "
        f"(division={division or 'All'}) from features={features_path}"
    )

    # Build report payload
    top_contenders = [
        {
            "rank": i,
            "fighter_id": row.get("fighter_id"),
            "name": row.get("name"),
            "score": round(r.rating, 3),
        }
        for i, (row, r) in enumerate(rated[:10], start=1)
    ]

    matchup_recommendations = []
    for row_a, row_b, sim, ps in selected[:5]:
        key_factors = sim.key_factors or explain_matchup(
            row_a, row_b, sim.rating_a, sim.rating_b
        )
        matchup_recommendations.append({
            "matchup": f"{row_a.get('name', row_a.get('fighter_id', ''))} vs "
                       f"{row_b.get('name', row_b.get('fighter_id', ''))}",
            "fighter_a_id": row_a.get("fighter_id", ""),
            "fighter_b_id": row_b.get("fighter_id", ""),
            "score_a": round(sim.rating_a, 3),
            "score_b": round(sim.rating_b, 3),
            "win_prob_a": sim.win_prob_a,
            "win_prob_b": sim.win_prob_b,
            "competitiveness": sim.competitiveness,
            "competitiveness_label": sim.competitiveness_label,
            "style_contrast": sim.style_contrast,
            "style_contrast_label": sim.style_contrast_label,
            "rank_impact": sim.rank_impact,
            "promoter_score": ps.total,
            "promoter_tier": ps.tier,
            "explanations": key_factors,
        })

    reports_dir = Path(args.reports_dir or "data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_data = {
        "division": division or "All",
        "top_contenders": top_contenders,
        "matchup_recommendations": matchup_recommendations,
    }
    report_path = reports_dir / "recommend.json"
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    log(f"Wrote {report_path}")

    md_path = reports_dir / "recommend.md"
    _write_division_markdown(md_path, division or "All", top_contenders, matchup_recommendations)
    log(f"Wrote {md_path}")

    # Terminal summary
    print(f"\n# FightMatch: {division or 'All divisions'}\n")
    print("## Top 10 contenders")
    for c in top_contenders:
        print(f"  {c['rank']}. {c.get('name', c.get('fighter_id', ''))}  ({c['score']:.2f})")
    print("\n## Recommended matchups")
    for i, rec in enumerate(matchup_recommendations, start=1):
        tier = rec.get("promoter_tier", "")
        ps_val = rec.get("promoter_score", 0.0)
        print(f"  {i}. {rec['matchup']}  [{tier} — {ps_val:.3f}]")
        print(f"     Win probability: {rec['win_prob_a']:.0%} / {rec['win_prob_b']:.0%}  "
              f"({rec['competitiveness_label']})")
        for reason in (rec.get("explanations") or [])[:3]:
            print(f"     • {reason}")
        print()

    return 0


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
            "No divisions detected. Run: fightmatch scrape ... && "
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
    all_rows = load_features_csv(features_path)

    summary_entries: list[dict] = []

    for _norm, label in divisions:
        division = label
        target = normalize_division(division)
        div_rows = [r for r in all_rows if normalize_division(r.get("weight_class")) == target]

        if not div_rows:
            log(f"Skipping division={division}: no fighters with features.")
            continue

        # Rate and rank fighters
        ratings = rate_all(div_rows)
        rated = sorted(zip(div_rows, ratings), key=lambda x: -x[1].rating)
        top_n_candidates = min(max(20, args.top * 2), len(rated))
        candidates = [(row, r.rating) for row, r in rated[:top_n_candidates]]

        selected = select_matchups_ranked(
            candidates,
            top_n=args.top,
            recent_pairs=recent_pairs,
            allow_short_notice=config.allow_short_notice,
        )
        if not selected:
            log(f"Skipping division={division}: could not form matchups.")
            continue

        top_contenders = [
            {
                "rank": i,
                "fighter_id": row.get("fighter_id"),
                "name": row.get("name"),
                "score": round(r.rating, 3),
            }
            for i, (row, r) in enumerate(rated[:10], start=1)
        ]

        matchup_recommendations = []
        for row_a, row_b, sim, ps in selected[:5]:
            key_factors = sim.key_factors or explain_matchup(
                row_a, row_b, sim.rating_a, sim.rating_b
            )
            matchup_recommendations.append({
                "matchup": f"{row_a.get('name', row_a.get('fighter_id', ''))} vs "
                           f"{row_b.get('name', row_b.get('fighter_id', ''))}",
                "fighter_a_id": row_a.get("fighter_id", ""),
                "fighter_b_id": row_b.get("fighter_id", ""),
                "score_a": round(sim.rating_a, 3),
                "score_b": round(sim.rating_b, 3),
                "win_prob_a": sim.win_prob_a,
                "win_prob_b": sim.win_prob_b,
                "competitiveness": sim.competitiveness,
                "competitiveness_label": sim.competitiveness_label,
                "style_contrast": sim.style_contrast,
                "style_contrast_label": sim.style_contrast_label,
                "rank_impact": sim.rank_impact,
                "promoter_score": ps.total,
                "promoter_tier": ps.tier,
                "explanations": key_factors,
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

        summary_entries.append({
            "division": division,
            "top_contenders": top_contenders[:3],
            "top_matchup": matchup_recommendations[0] if matchup_recommendations else None,
        })

    if not summary_entries:
        log("No divisions produced matchups; nothing to recommend.")
        return 1

    # Cross-division summary
    summary_path = reports_dir / "summary.md"
    with summary_path.open("w", encoding="utf-8") as f:
        ts = datetime.now().isoformat(timespec="seconds")
        f.write("# FightMatch summary\n\n")
        f.write(f"**Generated:** {ts}\n\n")
        f.write("## Divisions\n")
        for entry in summary_entries:
            f.write(f"- {entry['division']}\n")
        for entry in summary_entries:
            f.write(f"\n## {entry['division']}\n")
            f.write("Top 3 contenders:\n")
            for c in entry["top_contenders"]:
                name = c.get("name") or c.get("fighter_id") or ""
                score = float(c.get("score", 0.0))
                f.write(f"- {c.get('rank')}. {name} ({score:.2f})\n")
            top_matchup = entry.get("top_matchup")
            if top_matchup:
                f.write("\nTop matchup:\n")
                tier = top_matchup.get("promoter_tier", "")
                ps_val = top_matchup.get("promoter_score", top_matchup.get("score_a", 0.0))
                f.write(
                    f"- {top_matchup['matchup']} "
                    f"({top_matchup['score_a']:.2f} vs {top_matchup['score_b']:.2f})"
                    f"{f'  [{tier} — {float(ps_val):.3f}]' if tier else ''}\n"
                )
    log(f"Wrote {summary_path}")
    return 0


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
        prioritize_action=getattr(args, "prioritize_action", False),
        allow_short_notice=False,
        avoid_rematch=True,
    )
    rc = cmd_recommend_all(demo_args)
    if rc == 0:
        log(f"Demo complete. Reports written under {reports_dir}")
    return rc


# ── Argument parser ───────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="fightmatch",
        description="UFC analytics & matchmaking decision platform",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # scrape
    p_scrape = sub.add_parser("scrape", help="Scrape UFCStats since date")
    p_scrape.add_argument("--since", default="2020-01-01")
    p_scrape.add_argument("--out", default="data/raw")
    p_scrape.add_argument("--division", default="")
    p_scrape.set_defaults(func=cmd_scrape)

    # build-dataset
    p_build = sub.add_parser("build-dataset", help="Parse raw HTML into JSON/JSONL")
    p_build.add_argument("--raw", default="data/raw")
    p_build.add_argument("--out", default="data/processed")
    p_build.add_argument("--division", default="")
    p_build.set_defaults(func=cmd_build_dataset)

    # features
    p_feat = sub.add_parser("features", help="Build per-fighter features CSV")
    p_feat.add_argument("--in", dest="inp", default="data/processed")
    p_feat.add_argument("--out", default="data/features/features.csv")
    p_feat.add_argument("--division", default="")
    p_feat.set_defaults(func=cmd_features)

    # fighter-profile
    p_fp = sub.add_parser(
        "fighter-profile",
        help="Build a comprehensive analytics profile for a fighter",
    )
    p_fp.add_argument("--fighter", required=True, help="Fighter name (case-insensitive substring match)")
    p_fp.add_argument("--features", default="data/features/features.csv")
    p_fp.add_argument("--processed", default="data/processed")
    p_fp.add_argument("--reports-dir", default="data/reports")
    p_fp.set_defaults(func=cmd_fighter_profile)

    # simulate
    p_sim = sub.add_parser(
        "simulate",
        help="Run a matchup simulation between two fighters",
    )
    p_sim.add_argument("--fighter-a", required=True, dest="fighter_a")
    p_sim.add_argument("--fighter-b", required=True, dest="fighter_b")
    p_sim.add_argument("--features", default="data/features/features.csv")
    p_sim.add_argument("--processed", default="data/processed")
    p_sim.add_argument("--reports-dir", default="data/reports")
    p_sim.set_defaults(func=cmd_simulate)

    # recommend
    p_rec = sub.add_parser("recommend", help="Recommend matchups with promoter scoring")
    p_rec.add_argument("--division", default="")
    p_rec.add_argument("--top", type=int, default=10)
    p_rec.add_argument("--features", default="data/features/features.csv")
    p_rec.add_argument("--processed", default="data/processed")
    p_rec.add_argument("--reports-dir", default="data/reports")
    p_rec.add_argument("--prioritize-contender-clarity", action="store_true", default=True,
                       dest="prioritize_contender_clarity")
    p_rec.add_argument("--no-prioritize-contender-clarity", action="store_false",
                       dest="prioritize_contender_clarity")
    p_rec.add_argument("--prioritize-action", action="store_true", default=False,
                       dest="prioritize_action")
    p_rec.add_argument("--allow-short-notice", action="store_true", default=False,
                       dest="allow_short_notice")
    p_rec.add_argument("--avoid-rematch", action="store_true", default=True, dest="avoid_rematch")
    p_rec.add_argument("--no-avoid-rematch", action="store_false", dest="avoid_rematch")
    p_rec.set_defaults(func=cmd_recommend)

    # divisions
    p_div = sub.add_parser("divisions", help="List detected divisions")
    p_div.add_argument("--processed", default="data/processed")
    p_div.add_argument("--features", default="data/features/features.csv")
    p_div.set_defaults(func=cmd_divisions)

    # recommend-all
    p_rec_all = sub.add_parser("recommend-all", help="Recommend matchups for all divisions")
    p_rec_all.add_argument("--top", type=int, default=5)
    p_rec_all.add_argument("--features", default="data/features/features.csv")
    p_rec_all.add_argument("--processed", default="data/processed")
    p_rec_all.add_argument("--reports-dir", default="data/reports")
    p_rec_all.add_argument("--prioritize-contender-clarity", action="store_true", default=True,
                            dest="prioritize_contender_clarity")
    p_rec_all.add_argument("--no-prioritize-contender-clarity", action="store_false",
                            dest="prioritize_contender_clarity")
    p_rec_all.add_argument("--prioritize-action", action="store_true", default=False,
                            dest="prioritize_action")
    p_rec_all.add_argument("--allow-short-notice", action="store_true", default=False,
                            dest="allow_short_notice")
    p_rec_all.add_argument("--avoid-rematch", action="store_true", default=True, dest="avoid_rematch")
    p_rec_all.add_argument("--no-avoid-rematch", action="store_false", dest="avoid_rematch")
    p_rec_all.set_defaults(func=cmd_recommend_all)

    # demo
    p_demo = sub.add_parser("demo", help="Run a local FightMatch demo (no scraping)")
    p_demo.add_argument("--top", type=int, default=5)
    p_demo.add_argument("--processed", default="data/processed")
    p_demo.add_argument("--features", default="data/features/features.csv")
    p_demo.add_argument("--reports-dir", default="data/reports")
    p_demo.add_argument("--prioritize-action", action="store_true", default=False,
                        dest="prioritize_action")
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
