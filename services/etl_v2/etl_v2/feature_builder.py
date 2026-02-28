"""
Build pivot_fighter_fight_features: one row per (fight, fighter) with features
computed using ONLY fights strictly before the fight date (no leakage).
"""
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple

import psycopg2
from psycopg2.extras import execute_values

from .config import get_db_url


def _get_fights_and_participants(conn) -> List[Tuple]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT p.fight_id, p.fighter_id, p.opponent_id, p.is_winner, p.is_draw, p.finish_type,
                   f.date
            FROM pivot_fight_participants p
            JOIN pivot_fights f ON f.id = p.fight_id
            ORDER BY f.date, p.fight_id
        """)
        return cur.fetchall()


def _compute_features_for_row(
    conn,
    fight_id: str,
    fighter_id: str,
    opponent_id: str,
    fight_date: date,
    history: List[Tuple],
) -> dict:
    """
    history: list of (fight_id, fighter_id, opponent_id, is_winner, is_draw, finish_type, date)
    Only use rows where date < fight_date and fighter_id or opponent_id is our fighter/opponent.
    """
    fighter_history = [h for h in history if h[1] == fighter_id and h[6] < fight_date]
    opponent_history = [h for h in history if h[1] == opponent_id and h[6] < fight_date]

    # Activity: days_since_last_fight, fights_last_12m, fights_last_24m
    fighter_dates = sorted([h[6] for h in fighter_history], reverse=True)
    days_since_last_fight = None
    if fighter_dates:
        days_since_last_fight = (fight_date - fighter_dates[0]).days
    cut_12 = fight_date - timedelta(days=365)
    cut_24 = fight_date - timedelta(days=730)
    fights_last_12m = sum(1 for d in fighter_dates if d >= cut_12)
    fights_last_24m = sum(1 for d in fighter_dates if d >= cut_24)

    # Form: win_streak, last_n_results_summary (e.g. proportion of last 5 wins)
    wins = [h[3] for h in fighter_history if h[3] is not None and not h[4]]
    win_streak = 0
    for w in wins:
        if w:
            win_streak += 1
        else:
            break
    last_n = 5
    last_n_results = wins[:last_n]
    last_n_results_summary = (sum(last_n_results) / len(last_n_results)) if last_n_results else None

    # Experience
    total_fights_to_date = len(fighter_history)

    # Opponent strength: opponent_win_rate_to_date, opponent_win_streak_to_date
    opp_wins = [h[3] for h in opponent_history if h[3] is not None and not h[4]]
    opponent_win_rate_to_date = (sum(opp_wins) / len(opponent_history)) if opponent_history else None
    opponent_win_streak_to_date = 0
    for w in opp_wins:
        if w:
            opponent_win_streak_to_date += 1
        else:
            break

    # Finish rate: KO/sub as finish
    fighter_finishes = sum(1 for h in fighter_history if h[5] and str(h[5]).upper() in ("KO", "TKO", "KO/TKO", "SUB", "SUBMISSION"))
    fighter_finish_rate_to_date = (fighter_finishes / total_fights_to_date) if total_fights_to_date else None

    return {
        "fight_id": fight_id,
        "fighter_id": fighter_id,
        "opponent_id": opponent_id,
        "snapshot_date": fight_date,
        "days_since_last_fight": days_since_last_fight,
        "fights_last_12m": fights_last_12m,
        "fights_last_24m": fights_last_24m,
        "win_streak": win_streak,
        "last_n_results_summary": last_n_results_summary,
        "total_fights_to_date": total_fights_to_date,
        "opponent_win_rate_to_date": opponent_win_rate_to_date,
        "opponent_win_streak_to_date": opponent_win_streak_to_date,
        "fighter_finish_rate_to_date": fighter_finish_rate_to_date,
    }


def run_feature_builder(conn=None) -> int:
    if conn is None:
        conn = psycopg2.connect(get_db_url())
        own_conn = True
    else:
        own_conn = False
    try:
        rows = _get_fights_and_participants(conn)
        # Build list of (fight_id, fighter_id, opponent_id, is_winner, is_draw, finish_type, date)
        history = []
        for r in rows:
            history.append((str(r[0]), str(r[1]), str(r[2]), r[3], r[4], r[5], r[6]))

        with conn.cursor() as cur:
            cur.execute("DELETE FROM pivot_fighter_fight_features")
        inserted = 0
        for r in rows:
            fight_id, fighter_id, opponent_id, is_winner, is_draw, fight_date = str(r[0]), str(r[1]), str(r[2]), r[3], r[4], r[6]
            if is_draw:
                continue
            label_win = bool(is_winner) if is_winner is not None else False
            feats = _compute_features_for_row(conn, fight_id, fighter_id, opponent_id, fight_date, history)
            feats["label_win"] = label_win
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO pivot_fighter_fight_features (
                        fight_id, fighter_id, opponent_id, snapshot_date,
                        days_since_last_fight, fights_last_12m, fights_last_24m,
                        win_streak, last_n_results_summary, total_fights_to_date,
                        opponent_win_rate_to_date, opponent_win_streak_to_date,
                        fighter_finish_rate_to_date, label_win
                    ) VALUES %s
                    """,
                    [(
                        feats["fight_id"], feats["fighter_id"], feats["opponent_id"], feats["snapshot_date"],
                        feats["days_since_last_fight"], feats["fights_last_12m"], feats["fights_last_24m"],
                        feats["win_streak"], feats["last_n_results_summary"], feats["total_fights_to_date"],
                        feats["opponent_win_rate_to_date"], feats["opponent_win_streak_to_date"],
                        feats["fighter_finish_rate_to_date"], feats["label_win"],
                    )],
                )
            inserted += 1
        if own_conn:
            conn.commit()
        return inserted
    finally:
        if own_conn:
            conn.close()
