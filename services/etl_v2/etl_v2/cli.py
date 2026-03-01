import argparse
from pathlib import Path

from .ingest import run_ingest
from .feature_builder import run_feature_builder


def ingest_cmd() -> None:
    p = argparse.ArgumentParser(description="Ingest CSV data into pivot_* tables")
    p.add_argument("--data-dir", type=Path, default=Path("data"), help="Directory containing fighters.csv, fights.csv, fight_participants.csv")
    args = p.parse_args()
    out = run_ingest(args.data_dir)
    print("Ingested:", out)


def build_features_cmd() -> None:
    p = argparse.ArgumentParser(description="Build fighter_fight_features (no leakage)")
    p.parse_args()
    n = run_feature_builder()
    print(f"Built {n} feature rows")
