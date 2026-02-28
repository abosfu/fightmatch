# Modeling

Win-probability model + matchmaking engine.

1. **Train** (after ETL v2 ingest + build-features, and migrations applied):
   ```bash
   cd services/modeling && pip install -e .
   fightmatch-train
   ```
   Writes `reports/metrics.json`, `reports/calibration.png`, `models/logistic_regression.joblib`, `models/lightgbm.joblib`.

2. **Recommend** (ranked candidates with p_win and explanations):
   ```bash
   fightmatch-recommend --fighter_id <UUID> --weight_class "Lightweight" --top_k 10
   ```
   Or: `python -m modeling recommend --fighter_id X --weight_class Y`

Requires `DATABASE_URL`. Models must exist in `models/` (run train first).
