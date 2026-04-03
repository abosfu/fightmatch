"""CLI commands: fighter-profile, simulate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fightmatch.analytics.profile import (
    build_profile,
    format_profile_markdown,
    format_profile_terminal,
    profile_to_dict,
)
from fightmatch.analytics.rating import rate_all
from fightmatch.config import normalize_division
from fightmatch.engine.simulate import (
    format_simulation_markdown,
    format_simulation_terminal,
    simulate,
    simulation_to_dict,
)
from fightmatch.engine.whatif import SCENARIOS, format_whatif_terminal, run_whatif
from fightmatch.match import load_features_csv
from fightmatch.utils.log import log

from ._util import find_fighter_rows


def cmd_fighter_profile(args: argparse.Namespace) -> int:
    """Build and display a comprehensive analytics profile for a fighter."""
    features_path = Path(args.features)
    if not features_path.exists():
        log(f"Features file not found: {features_path}")
        return 1

    all_rows = load_features_csv(features_path)
    matches = find_fighter_rows(all_rows, args.fighter)

    if not matches:
        log(f"No fighter found matching: '{args.fighter}'")
        names = [r.get("name", "") for r in all_rows[:10] if r.get("name")]
        if names:
            log(f"Available fighters (first 10): {', '.join(names)}")
        else:
            log(
                "Features file appears empty. Run: fightmatch features --in data/processed --out ..."
            )
        return 1

    reports_dir = Path(args.reports_dir or "data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    for row in matches:
        division = row.get("weight_class", "")
        norm = normalize_division(division)
        division_rows = (
            [r for r in all_rows if normalize_division(r.get("weight_class")) == norm]
            if norm
            else all_rows
        )

        profile = build_profile(row, division_rows)
        print(format_profile_terminal(profile))

        fighter_slug = (
            (row.get("name") or row.get("fighter_id", "unknown"))
            .lower()
            .replace(" ", "_")
        )
        json_path = reports_dir / f"fighter_profile_{fighter_slug}.json"
        json_path.write_text(
            json.dumps(profile_to_dict(profile), indent=2), encoding="utf-8"
        )
        log(f"Wrote {json_path}")

        md_path = reports_dir / f"fighter_profile_{fighter_slug}.md"
        md_path.write_text(format_profile_markdown(profile), encoding="utf-8")
        log(f"Wrote {md_path}")

    if len(matches) > 1:
        log(
            f"Found {len(matches)} fighters matching '{args.fighter}'. Use a more specific name to narrow down."
        )

    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    """Run a matchup simulation between two named fighters."""
    features_path = Path(args.features)
    if not features_path.exists():
        log(f"Features file not found: {features_path}")
        return 1

    all_rows = load_features_csv(features_path)
    matches_a = find_fighter_rows(all_rows, args.fighter_a)
    matches_b = find_fighter_rows(all_rows, args.fighter_b)

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

    division_a = normalize_division(row_a.get("weight_class", ""))
    division_b = normalize_division(row_b.get("weight_class", ""))
    if division_a and division_b and division_a == division_b:
        division_rows = [
            r
            for r in all_rows
            if normalize_division(r.get("weight_class")) == division_a
        ]
    else:
        division_rows = all_rows

    ratings = rate_all(division_rows)
    ratings_sorted = sorted(ratings, key=lambda r: -r.rating)
    id_to_rank = {r.fighter_id: i + 1 for i, r in enumerate(ratings_sorted)}

    rank_a = id_to_rank.get(row_a.get("fighter_id", ""))
    rank_b = id_to_rank.get(row_b.get("fighter_id", ""))
    n_fighters = len(division_rows)

    sim = simulate(
        row_a,
        row_b,
        rank_pos_a=rank_a,
        rank_pos_b=rank_b,
        n_division_fighters=n_fighters,
    )
    print(format_simulation_terminal(sim))

    if getattr(args, "what_if", None):
        scenario_key = args.what_if
        if scenario_key not in SCENARIOS:
            log(
                f"Unknown what-if scenario: '{scenario_key}'. Valid options: {', '.join(SCENARIOS)}"
            )
        else:
            whatif_result = run_whatif(
                row_a,
                row_b,
                scenario_key,
                rank_pos_a=rank_a,
                rank_pos_b=rank_b,
                n_division_fighters=n_fighters,
            )
            if whatif_result:
                print(
                    format_whatif_terminal(whatif_result, sim.fighter_a, sim.fighter_b)
                )

    reports_dir = Path(args.reports_dir or "data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / "simulate.json"
    json_path.write_text(
        json.dumps(simulation_to_dict(sim), indent=2), encoding="utf-8"
    )
    log(f"Wrote {json_path}")

    md_path = reports_dir / "simulate.md"
    md_path.write_text(format_simulation_markdown(sim), encoding="utf-8")
    log(f"Wrote {md_path}")

    return 0
