"""FightMatch CLI entry point.

Usage:
    fightmatch <command> [options]
    python -m fightmatch.cli <command> [options]
"""

from __future__ import annotations

import argparse
import sys

from fightmatch.engine.whatif import SCENARIOS

from .analytics import cmd_fighter_profile, cmd_simulate
from .ingest import cmd_build_dataset, cmd_features, cmd_scrape
from .recommend import cmd_demo, cmd_divisions, cmd_recommend, cmd_recommend_all


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
        "fighter-profile", help="Build a comprehensive analytics profile for a fighter"
    )
    p_fp.add_argument(
        "--fighter",
        required=True,
        help="Fighter name (case-insensitive substring match)",
    )
    p_fp.add_argument("--features", default="data/features/features.csv")
    p_fp.add_argument("--processed", default="data/processed")
    p_fp.add_argument("--reports-dir", default="data/reports")
    p_fp.set_defaults(func=cmd_fighter_profile)

    # simulate
    p_sim = sub.add_parser(
        "simulate", help="Run a matchup simulation between two fighters"
    )
    p_sim.add_argument("--fighter-a", required=True, dest="fighter_a")
    p_sim.add_argument("--fighter-b", required=True, dest="fighter_b")
    p_sim.add_argument("--features", default="data/features/features.csv")
    p_sim.add_argument("--processed", default="data/processed")
    p_sim.add_argument("--reports-dir", default="data/reports")
    p_sim.add_argument(
        "--what-if",
        dest="what_if",
        default=None,
        metavar="SCENARIO",
        help=f"Run a what-if scenario on Fighter A. Options: {', '.join(SCENARIOS)}",
    )
    p_sim.set_defaults(func=cmd_simulate)

    # recommend
    p_rec = sub.add_parser("recommend", help="Recommend matchups with promoter scoring")
    p_rec.add_argument("--division", default="")
    p_rec.add_argument("--top", type=int, default=10)
    p_rec.add_argument("--features", default="data/features/features.csv")
    p_rec.add_argument("--processed", default="data/processed")
    p_rec.add_argument("--reports-dir", default="data/reports")
    p_rec.add_argument(
        "--prioritize-contender-clarity",
        action="store_true",
        default=True,
        dest="prioritize_contender_clarity",
    )
    p_rec.add_argument(
        "--no-prioritize-contender-clarity",
        action="store_false",
        dest="prioritize_contender_clarity",
    )
    p_rec.add_argument(
        "--prioritize-action",
        action="store_true",
        default=False,
        dest="prioritize_action",
    )
    p_rec.add_argument(
        "--allow-short-notice",
        action="store_true",
        default=False,
        dest="allow_short_notice",
    )
    p_rec.add_argument(
        "--avoid-rematch", action="store_true", default=True, dest="avoid_rematch"
    )
    p_rec.add_argument("--no-avoid-rematch", action="store_false", dest="avoid_rematch")
    p_rec.set_defaults(func=cmd_recommend)

    # divisions
    p_div = sub.add_parser("divisions", help="List detected divisions")
    p_div.add_argument("--processed", default="data/processed")
    p_div.add_argument("--features", default="data/features/features.csv")
    p_div.set_defaults(func=cmd_divisions)

    # recommend-all
    p_rec_all = sub.add_parser(
        "recommend-all", help="Recommend matchups for all divisions"
    )
    p_rec_all.add_argument("--top", type=int, default=5)
    p_rec_all.add_argument("--features", default="data/features/features.csv")
    p_rec_all.add_argument("--processed", default="data/processed")
    p_rec_all.add_argument("--reports-dir", default="data/reports")
    p_rec_all.add_argument(
        "--prioritize-contender-clarity",
        action="store_true",
        default=True,
        dest="prioritize_contender_clarity",
    )
    p_rec_all.add_argument(
        "--no-prioritize-contender-clarity",
        action="store_false",
        dest="prioritize_contender_clarity",
    )
    p_rec_all.add_argument(
        "--prioritize-action",
        action="store_true",
        default=False,
        dest="prioritize_action",
    )
    p_rec_all.add_argument(
        "--allow-short-notice",
        action="store_true",
        default=False,
        dest="allow_short_notice",
    )
    p_rec_all.add_argument(
        "--avoid-rematch", action="store_true", default=True, dest="avoid_rematch"
    )
    p_rec_all.add_argument(
        "--no-avoid-rematch", action="store_false", dest="avoid_rematch"
    )
    p_rec_all.set_defaults(func=cmd_recommend_all)

    # demo
    p_demo = sub.add_parser("demo", help="Run a local FightMatch demo (no scraping)")
    p_demo.add_argument("--top", type=int, default=5)
    p_demo.add_argument("--processed", default="data/processed")
    p_demo.add_argument("--features", default="data/features/features.csv")
    p_demo.add_argument("--reports-dir", default="data/reports")
    p_demo.add_argument(
        "--prioritize-action",
        action="store_true",
        default=False,
        dest="prioritize_action",
    )
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
