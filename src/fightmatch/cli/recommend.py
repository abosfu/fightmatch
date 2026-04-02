"""CLI commands: recommend, divisions, recommend-all, demo."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from fightmatch.analytics.landscape import build_landscape, format_landscape_terminal
from fightmatch.analytics.rating import rate_all
from fightmatch.config import MatchConfig, normalize_division
from fightmatch.engine.explain import explain_matchup_narrative
from fightmatch.engine.promoter import select_matchups_ranked
from fightmatch.match import explain_matchup, load_features_csv
from fightmatch.utils.log import log

from ._util import (
    detect_divisions,
    division_slug,
    load_recent_pairs,
    validate_local_data,
    write_division_markdown,
)


def cmd_recommend(args: argparse.Namespace) -> int:
    features_path = Path(args.features)
    processed_dir = Path(args.processed)

    if not features_path.exists():
        log(
            f"Features file not found: {features_path}. "
            f"Run: fightmatch features --in {processed_dir} --out {features_path} "
            f'--division "{args.division or "Welterweight"}"'
        )
        return 1

    config = MatchConfig(
        prioritize_contender_clarity=args.prioritize_contender_clarity,
        prioritize_action=args.prioritize_action,
        allow_short_notice=args.allow_short_notice,
        avoid_immediate_rematch=args.avoid_rematch,
    )
    division = args.division or ""

    all_rows = load_features_csv(features_path)
    target = normalize_division(division)
    div_rows = (
        [r for r in all_rows if normalize_division(r.get("weight_class")) == target]
        if target
        else all_rows
    )

    if not div_rows:
        if not all_rows:
            log(
                f"Features file {features_path} exists but contains zero rows. "
                f"Re-run: fightmatch features --in {processed_dir} --out {features_path}"
            )
        else:
            known = sorted(
                {r.get("weight_class", "") for r in all_rows if r.get("weight_class")}
            )
            log(
                f"No fighters found for division='{division}' in {features_path}. "
                f"Available divisions: {', '.join(known) or 'none detected'}. "
                f"Re-run with --division matching one of the above."
            )
        return 1

    ratings = rate_all(div_rows)
    rated = sorted(zip(div_rows, ratings), key=lambda x: -x[1].rating)
    top_n_candidates = min(max(20, args.top * 2), len(rated))
    candidates = [(row, r.rating) for row, r in rated[:top_n_candidates]]

    recent_pairs = load_recent_pairs(processed_dir)
    selected = select_matchups_ranked(
        candidates,
        top_n=args.top,
        recent_pairs=recent_pairs,
        allow_short_notice=config.allow_short_notice,
    )

    if not selected:
        log(
            f"Could not form matchups for division={division or 'All'} given current constraints."
        )
        return 1

    log(
        f"Recommend: contenders={len(candidates)}, matchups={len(selected)} "
        f"(division={division or 'All'}) from features={features_path}"
    )

    top_contenders = [
        {
            "rank": i,
            "fighter_id": row.get("fighter_id"),
            "name": row.get("name"),
            "score": round(r.rating, 3),
        }
        for i, (row, r) in enumerate(rated[:10], start=1)
    ]

    matchup_recommendations = _build_matchup_recs(selected[:5])

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
    write_division_markdown(
        md_path, division or "All", top_contenders, matchup_recommendations
    )
    log(f"Wrote {md_path}")

    print(f"\n# FightMatch: {division or 'All divisions'}\n")
    print("## Top 10 contenders")
    for c in top_contenders:
        print(
            f"  {c['rank']}. {c.get('name', c.get('fighter_id', ''))}  ({c['score']:.2f})"
        )
    print("\n## Recommended matchups")
    for i, rec in enumerate(matchup_recommendations, start=1):
        tier = rec.get("promoter_tier", "")
        ps_val = rec.get("promoter_score", 0.0)
        print(f"  {i}. {rec['matchup']}  [{tier} \u2014 {ps_val:.3f}]")
        print(
            f"     Win probability: {rec['win_prob_a']:.0%} / {rec['win_prob_b']:.0%}  "
            f"({rec['competitiveness_label']})"
        )
        for reason in (rec.get("explanations") or [])[:3]:
            print(f"     \u2022 {reason}")
        print()

    return 0


def cmd_divisions(args: argparse.Namespace) -> int:
    processed = Path(args.processed)
    features_path = Path(args.features) if args.features else None
    divisions = detect_divisions(processed, features_path)
    if not divisions:
        if not processed.exists():
            log(
                f"Processed data directory not found: {processed}. Run: fightmatch scrape ... && fightmatch build-dataset ..."
            )
        elif features_path and not features_path.exists():
            log(
                f"Features file not found: {features_path}. Run: fightmatch features --in {processed} --out {features_path}"
            )
        else:
            log(
                f"No divisions detected in {processed}. The processed dataset may be empty or the features CSV has no rows."
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
            f"Features file not found: {features_path}. Run: fightmatch features --in {processed_dir} --out {features_path}"
        )
        return 1

    divisions = detect_divisions(processed_dir, features_path)
    if not divisions:
        log(
            "No divisions detected. Run: fightmatch scrape ... && fightmatch build-dataset ... && fightmatch features ..."
        )
        return 1

    config = MatchConfig(
        prioritize_contender_clarity=args.prioritize_contender_clarity,
        prioritize_action=args.prioritize_action,
        allow_short_notice=args.allow_short_notice,
        avoid_immediate_rematch=args.avoid_rematch,
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    recent_pairs = load_recent_pairs(processed_dir)
    all_rows = load_features_csv(features_path)

    summary_entries: list[dict] = []
    n_divisions = len(divisions)

    for div_idx, (_, label) in enumerate(divisions, start=1):
        division = label
        log(f"[{div_idx}/{n_divisions}] Processing {division}...")
        target = normalize_division(division)
        div_rows = [
            r for r in all_rows if normalize_division(r.get("weight_class")) == target
        ]

        if not div_rows:
            log(f"  Skipping {division}: no fighters with features.")
            continue

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

        landscape = build_landscape(division, ratings)

        top_contenders = [
            {
                "rank": i,
                "fighter_id": row.get("fighter_id"),
                "name": row.get("name"),
                "score": round(r.rating, 3),
            }
            for i, (row, r) in enumerate(rated[:10], start=1)
        ]

        matchup_recommendations = _build_matchup_recs(selected[:5])

        slug = division_slug(division)
        json_path = reports_dir / f"{slug}.json"
        md_path = reports_dir / f"{slug}.md"
        report_data = {
            "division": division,
            "landscape": {
                "fighter_count": landscape.fighter_count,
                "active_count": landscape.active_count,
                "depth_score": landscape.depth_score,
                "activity_level": landscape.activity_level,
                "title_picture_clarity": landscape.title_picture_clarity,
                "logjam": landscape.logjam,
                "top_rated_fighter": landscape.top_rated_fighter,
                "rating_spread": landscape.rating_spread,
                "notes": landscape.notes,
            },
            "top_contenders": top_contenders,
            "matchup_recommendations": matchup_recommendations,
        }
        json_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        write_division_markdown(
            md_path, division, top_contenders, matchup_recommendations
        )
        log(f"  Wrote {json_path}")
        log(f"  Wrote {md_path}")

        print(format_landscape_terminal(landscape))
        summary_entries.append(
            {
                "division": division,
                "top_contenders": top_contenders[:3],
                "top_matchup": matchup_recommendations[0]
                if matchup_recommendations
                else None,
            }
        )

    if not summary_entries:
        log("No divisions produced matchups; nothing to recommend.")
        return 1

    _write_summary(reports_dir / "summary.md", summary_entries)
    log(f"Wrote {reports_dir / 'summary.md'}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Run recommend-all across all detected divisions using real local data."""
    processed_dir = Path(args.processed)
    features_path = Path(args.features)
    reports_dir = Path(args.reports_dir or "data/reports")

    ok, reason = validate_local_data(processed_dir, features_path)
    if not ok:
        log(reason)
        return 1

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
    divisions = detect_divisions(processed_dir, features_path)
    log(f"Demo: {len(divisions)} division(s) detected. Running recommend-all...")
    rc = cmd_recommend_all(demo_args)
    if rc == 0:
        written = list(reports_dir.glob("*.json")) if reports_dir.exists() else []
        log(
            f"Demo complete. {len(written)} report file(s) written under {reports_dir}. "
            f"See {reports_dir / 'summary.md'} for the cross-division overview."
        )
    return rc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_matchup_recs(selected: list) -> list[dict]:
    recs = []
    for row_a, row_b, sim, ps in selected:
        narrative = explain_matchup_narrative(sim, ps)
        key_factors = (
            list(sim.key_factors) + narrative
            if sim.key_factors
            else (
                narrative or explain_matchup(row_a, row_b, sim.rating_a, sim.rating_b)
            )
        )
        recs.append(
            {
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
            }
        )
    return recs


def _write_summary(path: Path, entries: list[dict]) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    with path.open("w", encoding="utf-8") as f:
        f.write("# FightMatch summary\n\n")
        f.write(f"**Generated:** {ts}\n\n")
        f.write("## Divisions\n")
        for entry in entries:
            f.write(f"- {entry['division']}\n")
        for entry in entries:
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
                ps_val = top_matchup.get(
                    "promoter_score", top_matchup.get("score_a", 0.0)
                )
                tier_suffix = f"  [{tier} \u2014 {float(ps_val):.3f}]" if tier else ""
                f.write(
                    f"- {top_matchup['matchup']} "
                    f"({top_matchup['score_a']:.2f} vs {top_matchup['score_b']:.2f})"
                    f"{tier_suffix}\n"
                )
