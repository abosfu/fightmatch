"""
Matchmaking engine: filter by hard constraints, rank by multi-objective score
using p_win + activity/competitiveness proxies. Explainability: constraints passed/failed, score components.
"""
import json
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd
import psycopg2
import joblib

from .config import get_db_url, get_models_dir
from .data import FEATURE_COLS

# Default constraints (can be overridden)
MAX_DAYS_INACTIVE = 400
MIN_FIGHTS_RECENT = 0


def load_model(name: str = "lightgbm"):
    models_dir = get_models_dir()
    path = models_dir / f"{name}.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


def get_candidates_for_fighter(fighter_id: str, weight_class: str, db_url: str = None) -> pd.DataFrame:
    """Return all fighters in the same weight class except the given fighter."""
    if db_url is None:
        db_url = get_db_url()
    conn = psycopg2.connect(db_url)
    df = pd.read_sql(
        """
        SELECT id, name, weight_class FROM pivot_fighters
        WHERE weight_class = %s AND id != %s
        """,
        conn,
        params=(weight_class, fighter_id),
    )
    conn.close()
    return df


def get_latest_features_for_fighter(fighter_id: str, db_url: str = None) -> Optional[dict]:
    """Get the most recent feature row for a fighter (for activity/form proxies)."""
    if db_url is None:
        db_url = get_db_url()
    conn = psycopg2.connect(db_url)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT days_since_last_fight, fights_last_12m, win_streak, total_fights_to_date,
                   fighter_finish_rate_to_date
            FROM pivot_fighter_fight_features
            WHERE fighter_id = %s
            ORDER BY snapshot_date DESC LIMIT 1
            """,
            (fighter_id,),
        )
        row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "days_since_last_fight": row[0],
        "fights_last_12m": row[1],
        "win_streak": row[2],
        "total_fights_to_date": row[3],
        "fighter_finish_rate_to_date": row[4],
    }


def build_feature_row_for_matchup(
    fighter_id: str,
    opponent_id: str,
    fighter_proxy: dict,
    opponent_proxy: dict,
) -> dict:
    """Build a single feature dict for (fighter vs opponent) using proxy stats. For MVP we use simple averages/placeholders."""
    return {
        "days_since_last_fight": fighter_proxy.get("days_since_last_fight") or 180,
        "fights_last_12m": fighter_proxy.get("fights_last_12m") or 1,
        "fights_last_24m": (fighter_proxy.get("fights_last_12m") or 1) * 2,
        "win_streak": fighter_proxy.get("win_streak") or 0,
        "last_n_results_summary": 0.5,
        "total_fights_to_date": fighter_proxy.get("total_fights_to_date") or 5,
        "opponent_win_rate_to_date": 0.5,
        "opponent_win_streak_to_date": opponent_proxy.get("win_streak") or 0,
        "fighter_finish_rate_to_date": fighter_proxy.get("fighter_finish_rate_to_date") or 0.5,
    }


def check_constraints(proxy: dict) -> tuple[bool, List[str]]:
    passed = True
    reasons = []
    if (proxy.get("days_since_last_fight") or 0) > MAX_DAYS_INACTIVE:
        passed = False
        reasons.append(f"inactive_over_{MAX_DAYS_INACTIVE}_days")
    if (proxy.get("fights_last_12m") or 0) < MIN_FIGHTS_RECENT:
        pass
    return passed, reasons


def recommend(
    fighter_id: str,
    weight_class: str,
    model_name: str = "lightgbm",
    top_k: int = 10,
    db_url: str = None,
) -> List[dict]:
    """
    Return ranked candidates with p_win, constraints_passed/failed, score components.
    """
    if db_url is None:
        db_url = get_db_url()
    model = load_model(model_name)
    candidates_df = get_candidates_for_fighter(fighter_id, weight_class, db_url)
    fighter_proxy = get_latest_features_for_fighter(fighter_id, db_url) or {}
    results = []
    for _, row in candidates_df.iterrows():
        opp_id = row["id"]
        opp_name = row["name"]
        opponent_proxy = get_latest_features_for_fighter(opp_id, db_url) or {}
        constraints_passed, constraints_failed = check_constraints(opponent_proxy)
        feats = build_feature_row_for_matchup(fighter_id, opp_id, fighter_proxy, opponent_proxy)
        X = pd.DataFrame([feats])[FEATURE_COLS].fillna(0)
        p_win = float(model.predict_proba(X)[0, 1]) if model is not None else 0.5
        # Multi-objective score: p_win + activity proxy (higher fights_last_12m = more active) + competitiveness (closer p_win to 0.5)
        activity_score = min(1.0, (feats["fights_last_12m"] or 0) / 3.0)
        competitiveness = 1.0 - 2 * abs(p_win - 0.5)
        total_score = 0.5 * p_win + 0.3 * activity_score + 0.2 * max(0, competitiveness)
        results.append({
            "opponent_id": opp_id,
            "opponent_name": opp_name,
            "p_win": round(p_win, 4),
            "constraints_passed": constraints_passed,
            "constraints_failed": constraints_failed,
            "score_components": {
                "p_win": round(p_win, 4),
                "activity": round(activity_score, 4),
                "competitiveness": round(max(0, competitiveness), 4),
            },
            "total_score": round(total_score, 4),
        })
    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results[:top_k]


def recommend_cli_output(fighter_id: str, weight_class: str, model_name: str = "lightgbm", top_k: int = 10) -> str:
    out = recommend(fighter_id, weight_class, model_name=model_name, top_k=top_k)
    return json.dumps({"fighter_id": fighter_id, "weight_class": weight_class, "candidates": out}, indent=2)
