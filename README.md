# FightMatch

**UFC matchmaking + rankings decision support.** No UI — output is terminal text and JSON/CSV artifacts. Data-backed from [UFCStats](https://www.ufcstats.com); no mock data or hardcoding.

## What this is

- **Decision-support tool** for ranking and matchup ideas: ingest real UFC fight and fighter stats, build a structured dataset, compute ranking signals and matchup scores, and print recommended matchups with short explanations (why this fight makes sense).
- Matchmaking is modeled from **public performance/recency/activity/style/ranking proxies**. Business constraints (contender clarity vs high-profile, action-focused, short-notice) are configurable knobs.

## Install

```bash
pip install -e .
```

With dev deps (pytest):

```bash
pip install -e ".[dev]"
```

## Commands

| Command | Description |
|--------|-------------|
| `fightmatch scrape --since YYYY-MM-DD --out data/raw` | Discover events since date, fetch event and fight pages (rate-limited, cached) |
| `fightmatch build-dataset --raw data/raw --out data/processed` | Parse raw HTML into normalized JSON/JSONL |
| `fightmatch features --in data/processed --out data/features/features.csv` | Build per-fighter rolling features CSV |
| `fightmatch recommend --division "Lightweight" --top 10` | Print recommended matchups with explanations |

### Example terminal output

```text
# FightMatch recommended matchups
# Division: Lightweight

## 1. Fighter A vs Fighter B
   Rank scores: 2.450 vs 2.320
   - Both top-8 by rank score, within 0.13 points
   - Fighter A on 3-fight streak; Fighter B on 1-fight streak
   - Opponent quality proxy: A 0.62, B 0.58 in last fights
   - Striking/grappling mix: A 5.2 sig/min, 1.2 TD att/15; B 4.1 sig/min, 3.0 TD att/15
   - Both active within last 180 days (good booking probability proxy)
```

## Data ethics

- **Rate limit**: 1 request/sec with jitter to UFCStats.
- **Caching**: Raw HTML cached to disk with TTL (default 7 days) to avoid repeat hits.
- **Retries**: Backoff on failures; clear User-Agent string.
- No mock data; tests use minimal fixture HTML only.

## Layout

```
.
├── pyproject.toml
├── README.md
├── src/fightmatch/
│   ├── cli.py           # scrape | build-dataset | features | recommend
│   ├── config.py
│   ├── cache.py
│   ├── scrape/          # UFCStats client, parse, schemas
│   ├── data/             # store, features
│   ├── match/            # rank, score, explain
│   └── utils/
├── tests/
└── .github/workflows/ci.yml
```

## Artifacts

- `data/raw/ufcstats/` — Cached HTML (events, fights).
- `data/processed/` — `fighters.json`, `events.json`, `bouts.json`, `stats.jsonl`.
- `data/features/features.csv` — Per-fighter features (recency, win streak, sig/min, TD rate, finish rate, opponent quality proxy, etc.).

## Requirements

- Python 3.11 or 3.12
- requests, beautifulsoup4, pydantic
