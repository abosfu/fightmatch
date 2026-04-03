# Data (gitignored)

Place reproducible dataset CSVs here for the pivot pipeline:

- `fighters.csv`: id, name, weight_class, stance, dob
- `fights.csv`: id, date, weight_class, method, round
- `fight_participants.csv`: fight_id, fighter_id, opponent_id, is_winner, is_draw, finish_type

Then run: `fightmatch-ingest --data-dir .` from `services/etl_v2` (or pass this directory).

Ids should be UUIDs. Dates: YYYY-MM-DD. is_winner: true/false or 1/0.
