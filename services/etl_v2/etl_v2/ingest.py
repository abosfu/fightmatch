"""
Ingest CSV or seed data into pivot_* tables.
Expects CSVs: fighters.csv, fights.csv, fight_participants.csv
(or a single seed CSV with columns compatible with pivot schema).
"""
import csv
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Optional

import psycopg2
from psycopg2.extras import execute_values

from .config import get_db_url

# Default column names for CSVs (can be overridden)
FIGHTERS_COLS = ["id", "name", "weight_class", "stance", "dob"]
FIGHTS_COLS = ["id", "date", "weight_class", "method", "round"]
PARTICIPANTS_COLS = ["fight_id", "fighter_id", "opponent_id", "is_winner", "is_draw", "finish_type"]


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s or s.strip() == "":
        return None
    try:
        return date.fromisoformat(s.strip()[:10])
    except ValueError:
        return None


def ingest_fighters_csv(conn, path: Path) -> int:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            fid = r.get("id") or str(uuid.uuid4())
            dob = _parse_date(r.get("dob"))
            rows.append((fid, r.get("name", ""), r.get("weight_class", ""), r.get("stance") or None, dob))
    if not rows:
        return 0
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO pivot_fighters (id, name, weight_class, stance, dob)
            VALUES %s ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name, weight_class = EXCLUDED.weight_class,
            stance = EXCLUDED.stance, dob = EXCLUDED.dob
            """,
            rows,
        )
    return len(rows)


def ingest_fights_csv(conn, path: Path) -> int:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            fid = r.get("id") or str(uuid.uuid4())
            d = _parse_date(r.get("date"))
            if not d:
                continue
            rnd = r.get("round")
            rows.append((fid, d, r.get("weight_class", ""), r.get("method") or None, int(rnd) if rnd and str(rnd).isdigit() else None))
    if not rows:
        return 0
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO pivot_fights (id, date, weight_class, method, round)
            VALUES %s ON CONFLICT (id) DO UPDATE SET
            date = EXCLUDED.date, weight_class = EXCLUDED.weight_class,
            method = EXCLUDED.method, round = EXCLUDED.round
            """,
            rows,
        )
    return len(rows)


def ingest_participants_csv(conn, path: Path) -> int:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            fight_id = r.get("fight_id")
            fighter_id = r.get("fighter_id")
            opponent_id = r.get("opponent_id")
            if not all([fight_id, fighter_id, opponent_id]):
                continue
            is_winner = r.get("is_winner", "").strip().lower() in ("1", "true", "yes")
            is_draw = r.get("is_draw", "").strip().lower() in ("1", "true", "yes")
            finish_type = r.get("finish_type") or None
            rows.append((fight_id, fighter_id, opponent_id, is_winner, is_draw, finish_type))
    if not rows:
        return 0
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO pivot_fight_participants (fight_id, fighter_id, opponent_id, is_winner, is_draw, finish_type)
            VALUES %s ON CONFLICT (fight_id, fighter_id) DO UPDATE SET
            opponent_id = EXCLUDED.opponent_id, is_winner = EXCLUDED.is_winner,
            is_draw = EXCLUDED.is_draw, finish_type = EXCLUDED.finish_type
            """,
            rows,
        )
    return len(rows)


def run_ingest(
    data_dir: Path,
    fighters_csv: str = "fighters.csv",
    fights_csv: str = "fights.csv",
    participants_csv: str = "fight_participants.csv",
) -> dict:
    conn = psycopg2.connect(get_db_url())
    conn.autocommit = False
    try:
        n_f = ingest_fighters_csv(conn, data_dir / fighters_csv) if (data_dir / fighters_csv).exists() else 0
        n_fi = ingest_fights_csv(conn, data_dir / fights_csv) if (data_dir / fights_csv).exists() else 0
        n_p = ingest_participants_csv(conn, data_dir / participants_csv) if (data_dir / participants_csv).exists() else 0
        conn.commit()
        return {"fighters": n_f, "fights": n_fi, "participants": n_p}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
