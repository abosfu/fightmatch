"""
Train Logistic Regression + LightGBM, evaluate AUC, log loss, Brier, calibration.
Save metrics.json and calibration.png to reports/.
"""
import json
import joblib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import calibration_curve
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .data import load_features, time_split, FEATURE_COLS
from .config import get_reports_dir, get_models_dir


def prepare_xy(df: pd.DataFrame):
    df = df.copy()
    for c in FEATURE_COLS:
        if df[c].dtype == object or str(df[c].dtype) == "object":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df[FEATURE_COLS] = df[FEATURE_COLS].fillna(0)
    X = df[FEATURE_COLS].astype(np.float64)
    y = df["label_win"].astype(int)
    return X, y


def train_and_evaluate(db_url: str = None) -> dict:
    df = load_features(db_url)
    if len(df) < 20:
        raise ValueError("Need at least 20 feature rows; run ingest + build-features first")
    train_df, test_df = time_split(df, test_fraction=0.2)
    X_train, y_train = prepare_xy(train_df)
    X_test, y_test = prepare_xy(test_df)

    metrics = {}

    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    proba_lr = lr.predict_proba(X_test)[:, 1]
    metrics["logistic_regression"] = {
        "auc": float(roc_auc_score(y_test, proba_lr)),
        "log_loss": float(log_loss(y_test, proba_lr)),
        "brier": float(brier_score_loss(y_test, proba_lr)),
    }

    # LightGBM
    lg = lgb.LGBMClassifier(n_estimators=100, max_depth=5, random_state=42, verbosity=-1)
    lg.fit(X_train, y_train)
    proba_lgb = lg.predict_proba(X_test)[:, 1]
    metrics["lightgbm"] = {
        "auc": float(roc_auc_score(y_test, proba_lgb)),
        "log_loss": float(log_loss(y_test, proba_lgb)),
        "brier": float(brier_score_loss(y_test, proba_lgb)),
    }

    # Calibration curve (use LightGBM as primary for plot)
    frac_pos, mean_pred = calibration_curve(y_test, proba_lgb, n_bins=10)
    reports_dir = get_reports_dir()
    fig, ax = plt.subplots()
    ax.plot(mean_pred, frac_pos, "s-", label="LightGBM")
    ax.plot([0, 1], [0, 1], "k--", label="Perfect")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title("Calibration curve (test set)")
    ax.legend()
    fig.savefig(reports_dir / "calibration.png", dpi=100, bbox_inches="tight")
    plt.close()

    with open(reports_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    models_dir = get_models_dir()
    joblib.dump(lr, models_dir / "logistic_regression.joblib")
    joblib.dump(lg, models_dir / "lightgbm.joblib")

    return metrics
