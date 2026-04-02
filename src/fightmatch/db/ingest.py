"""Ingest fighter data from features CSV into fightmatch.db.

Usage
-----
    python -m fightmatch.db.ingest
    python -m fightmatch.db.ingest --features path/to/features.csv
    python -m fightmatch.db.ingest --processed-dir path/to/processed --features path/to/features.csv

Source files
    features/features.csv  → fighters table  (primary source of fighter data)
    processed/bouts.json   → bouts table     (optional — only if non-empty)
    processed/events.json  → events table    (optional — only if non-empty)
    processed/stats.jsonl  → fight_stats table (optional — only if non-empty)
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from .models import Base, Bout, Event, Fighter, FightStats, SessionLocal, engine

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_FEATURES = _PROJECT_ROOT / "data" / "features" / "features.csv"
_DEFAULT_PROCESSED = _PROJECT_ROOT / "data" / "processed"


def _load_csv(path: Path) -> list[dict]:
    if not path.exists():
        logger.warning("Skipping %s — file not found.", path)
        return []
    records: list[dict] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            records.append(row)
    logger.info("Loaded %d records from %s", len(records), path)
    return records


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        logger.warning("Skipping %s — file not found.", path)
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        logger.warning(
            "Expected a JSON array in %s, got %s — skipping.", path, type(data).__name__
        )
        return []
    if not data:
        return []
    logger.info("Loaded %d records from %s", len(data), path)
    return data


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        logger.warning("Skipping %s — file not found.", path)
        return []
    records: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                logger.warning("Skipping line %d in %s: %s", lineno, path, exc)
    if records:
        logger.info("Loaded %d records from %s", len(records), path)
    return records


def _safe_float(val: str | None) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val: str | None) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def ingest_fighters_from_csv(session, features_path: Path) -> int:
    """Read features.csv and upsert into the fighters table.

    The CSV has: fighter_id, name, weight_class, activity_recency_days,
    win_streak, last_5_win_pct, sig_str_diff_per_min, td_rate,
    td_attempts_per_15, control_per_15, finish_rate, opponent_recent_win_pct_avg.

    We map these into the Fighter model. Fields not present in the CSV
    (height, reach, stance, dob) are left NULL.
    """
    records = _load_csv(features_path)
    if not records:
        logger.warning(
            "No fighter rows found in %s. Is the CSV populated?", features_path
        )
        return 0

    inserted = skipped = 0
    for row in records:
        fid = (row.get("fighter_id") or "").strip()
        if not fid:
            skipped += 1
            continue
        fighter = Fighter(
            fighter_id=fid,
            name=(row.get("name") or fid).strip(),
            height=None,
            reach=None,
            stance=None,
            dob=None,
        )
        try:
            session.merge(fighter)
            session.flush()
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1

    logger.info("fighters  — upserted %d, skipped %d", inserted, skipped)
    return inserted


def ingest_events(session, processed_dir: Path) -> None:
    records = _load_json(processed_dir / "events.json")
    if not records:
        return
    inserted = skipped = 0
    for raw in records:
        obj = Event(**{k: v for k, v in raw.items() if hasattr(Event, k)})
        try:
            session.merge(obj)
            session.flush()
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
    logger.info("events    — upserted %d, skipped %d", inserted, skipped)


def ingest_bouts(session, processed_dir: Path) -> None:
    records = _load_json(processed_dir / "bouts.json")
    if not records:
        return
    inserted = skipped = 0
    for raw in records:
        obj = Bout(**{k: v for k, v in raw.items() if hasattr(Bout, k)})
        try:
            session.merge(obj)
            session.flush()
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
    logger.info("bouts     — upserted %d, skipped %d", inserted, skipped)


def ingest_fight_stats(session, processed_dir: Path) -> None:
    records = _load_jsonl(processed_dir / "stats.jsonl")
    if not records:
        return
    existing = {
        (r.bout_id, r.fighter_id, r.corner)
        for r in session.query(
            FightStats.bout_id, FightStats.fighter_id, FightStats.corner
        )
    }
    inserted = skipped = 0
    for raw in records:
        key = (raw.get("bout_id"), raw.get("fighter_id"), raw.get("corner"))
        if key in existing:
            skipped += 1
            continue
        obj = FightStats(**{k: v for k, v in raw.items() if hasattr(FightStats, k)})
        session.add(obj)
        existing.add(key)
        inserted += 1
    session.flush()
    logger.info("fight_stats — inserted %d, skipped %d duplicates", inserted, skipped)


def run(
    features_path: Path | None = None,
    processed_dir: Path | None = None,
) -> None:
    features_path = features_path or _DEFAULT_FEATURES
    processed_dir = processed_dir or _DEFAULT_PROCESSED

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s  %(message)s",
        stream=sys.stdout,
    )

    logger.info("Creating schema in %s", engine.url)
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        count = ingest_fighters_from_csv(session, features_path)
        if count == 0:
            logger.warning(
                "No fighters ingested. Make sure data exists by running:\n"
                "  fightmatch scrape --since 2023-01-01 --out data/raw\n"
                "  fightmatch build-dataset --raw data/raw --out data/processed\n"
                "  fightmatch features --in data/processed --out data/features/features.csv"
            )
        ingest_events(session, processed_dir)
        ingest_bouts(session, processed_dir)
        ingest_fight_stats(session, processed_dir)
        session.commit()

    logger.info("Ingestion complete.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest FightMatch data into fightmatch.db"
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=None,
        help="Path to features CSV (default: data/features/features.csv)",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help="Path to the processed data directory (default: data/processed/)",
    )
    args = parser.parse_args()
    run(features_path=args.features, processed_dir=args.processed_dir)


if __name__ == "__main__":
    main()
