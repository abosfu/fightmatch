# FightMatch

Data-backed decision-support system for UFC matchmaking: **reproducible dataset → win-probability model → constrained matchmaking engine** with explainability.

## Pivot pipeline (MVP)

1. **Data** — Postgres-backed dataset with a feature table of "fighter before this fight" rows (no leakage).
2. **Model** — Train and evaluate a baseline (Logistic Regression + LightGBM); time-based train/test split; AUC, log loss, Brier, calibration.
3. **Matchmaking** — Filter candidates by hard constraints; rank by multi-objective score (p_win + activity/competitiveness); expose constraints passed/failed and score components.

## Project structure

```
fightmatch/
├── apps/web/                 # Next.js app (demo + optional Supabase UI)
├── services/
│   ├── etl/                  # Legacy ETL
│   ├── etl_v2/               # Ingest + feature builder (no leakage)
│   └── modeling/             # Train, evaluate, matchmaking engine
├── infra/db/migrations/      # Pivot schema (pivot_* tables)
├── data/                     # CSV dataset (gitignored)
├── reports/                  # metrics.json, calibration.png (gitignored)
├── models/                   # Saved models (gitignored)
└── packages/shared/          # Shared types
```

## Quick start (pipeline)

1. **Postgres** — Create a DB and run migrations:
   ```bash
   psql $DATABASE_URL -f infra/db/migrations/001_pivot_schema.sql
   ```

2. **Dataset** — Place CSVs in `data/`: `fighters.csv`, `fights.csv`, `fight_participants.csv` (see `data/README.md`). Then:
   ```bash
   cd services/etl_v2 && pip install -e . && fightmatch-ingest --data-dir ../../data && fightmatch-build-features
   ```

3. **Train** — Time-based split, train LR + LightGBM, write metrics and artifacts:
   ```bash
   cd services/modeling && pip install -e . && fightmatch-train
   ```
   Outputs: `reports/metrics.json`, `reports/calibration.png`, `models/*.joblib`.

4. **Recommend** — Ranked candidates with p_win and explanations:
   ```bash
   fightmatch-recommend --fighter_id <UUID> --weight_class "Lightweight" --top_k 10
   ```

5. **API** — Thin Next.js route that calls the engine:  
   `GET /api/matchmaking?fighter_id=&weight_class=` (requires `DATABASE_URL` and trained model).

## CLI summary

| Command | Description |
|--------|-------------|
| `fightmatch-ingest --data-dir <dir>` | Ingest CSVs into pivot_* tables |
| `fightmatch-build-features` | Build fighter_fight_features (pre-fight only) |
| `fightmatch-train` | Train models, evaluate, save metrics + models |
| `fightmatch-recommend --fighter_id X --weight_class Y` | Matchmaking: ranked list + p_win + constraints + score components |

## Web app

- **Demo mode** (no env): `pnpm install && pnpm -C apps/web dev` — mock data, no Supabase.
- **Supabase**: set `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` in `apps/web/.env.local`; run `supabase/migrations` and seed.

## Tech stack

- **Data**: Postgres, pandas, psycopg2
- **Model**: scikit-learn (LogisticRegression), LightGBM
- **App**: Next.js 14, TypeScript, Supabase (optional)
