# ETL v2

Ingest and feature builder for the FightMatch pivot pipeline.

- **ingest**: Load `fighters.csv`, `fights.csv`, `fight_participants.csv` from `--data-dir` (default `data/`) into `pivot_*` tables.
- **build-features**: Compute `pivot_fighter_fight_features` using only fights **before** each fight date (no leakage).

Requires `DATABASE_URL` (env or `services/etl_v2/.env`). Run migrations in `infra/db/migrations/` first.

```bash
cd services/etl_v2 && pip install -e . && fightmatch-ingest --data-dir ../../data && fightmatch-build-features
```
