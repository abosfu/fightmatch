"""
Load pivot_fighter_fight_features from Postgres and time-based train/test split.
"""
import pandas as pd
import psycopg2

from .config import get_db_url

FEATURE_COLS = [
    "days_since_last_fight",
    "fights_last_12m",
    "fights_last_24m",
    "win_streak",
    "last_n_results_summary",
    "total_fights_to_date",
    "opponent_win_rate_to_date",
    "opponent_win_streak_to_date",
    "fighter_finish_rate_to_date",
]


def load_features(db_url: str = None) -> pd.DataFrame:
    if db_url is None:
        db_url = get_db_url()
    conn = psycopg2.connect(db_url)
    df = pd.read_sql(
        """
        SELECT id, fight_id, fighter_id, opponent_id, snapshot_date,
               days_since_last_fight, fights_last_12m, fights_last_24m,
               win_streak, last_n_results_summary, total_fights_to_date,
               opponent_win_rate_to_date, opponent_win_streak_to_date,
               fighter_finish_rate_to_date, label_win
        FROM pivot_fighter_fight_features
        ORDER BY snapshot_date
        """,
        conn,
    )
    conn.close()
    return df


def time_split(df: pd.DataFrame, test_fraction: float = 0.2):
    """
    Train on older fights, test on newer. test_fraction of the latest rows are test.
    """
    df = df.sort_values("snapshot_date").reset_index(drop=True)
    n = len(df)
    n_test = max(1, int(n * test_fraction))
    n_train = n - n_test
    train_df = df.iloc[:n_train]
    test_df = df.iloc[n_train:]
    return train_df, test_df
