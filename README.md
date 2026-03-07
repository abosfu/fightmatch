# FightMatch

**FightMatch** is a CLI-first UFC matchmaking and analytics tool. It ingests real fight data from `ufcstats.com`, builds a structured dataset, ranks fighters within each division, and recommends matchups with short, human-readable explanations.

## What FightMatch is

- **Data-backed decision support** for UFC matchmaking: rankings, contender clarity, and style-test ideas.
- **Division-aware**: works across all UFC divisions detected in the processed dataset.
- **Artifact-first**: produces machine-readable JSON and human-readable Markdown reports, suitable for portfolios and lightweight analytics workflows.

## Why it exists

- To demonstrate a **production-like analytics pipeline** on real-world sports data (scraping → dataset → features → rankings → recommendations).
- To provide a **clean, recruiter-friendly codebase**: minimal dependencies, offline tests, and a clear end-to-end story.
- To explore **matchmaking heuristics** (activity, rank gaps, rematch avoidance, style clashes) in a way that’s transparent and configurable.

## Install

```bash
pip install -e .
```

With dev deps (pytest):

```bash
pip install -e ".[dev]"
```

## End-to-end workflow

1. **Scrape UFCStats** (events + fights, rate-limited, cached):

   ```bash
   fightmatch scrape --since 2023-01-01 --out data/raw
   ```

2. **Build processed dataset** (fighters, events, bouts, stats):

   ```bash
   fightmatch build-dataset --raw data/raw --out data/processed
   ```

3. **Build per-fighter features** (across all divisions):

   ```bash
   fightmatch features --in data/processed --out data/features/features.csv
   ```

4. **Inspect available divisions**:

   ```bash
   fightmatch divisions --processed data/processed --features data/features/features.csv
   ```

5. **Generate recommendations**:

   - Single division:

     ```bash
     fightmatch recommend \
       --division "Welterweight" \
       --top 10 \
       --features data/features/features.csv \
       --processed data/processed \
       --reports-dir data/reports
     ```

   - All detected divisions:

     ```bash
     fightmatch recommend-all \
       --top 5 \
       --features data/features/features.csv \
       --processed data/processed \
       --reports-dir data/reports
     ```

## Core commands

- **Scrape**
  - `fightmatch scrape --since YYYY-MM-DD --out data/raw`
- **Dataset**
  - `fightmatch build-dataset --raw data/raw --out data/processed`
- **Features**
  - `fightmatch features --in data/processed --out data/features/features.csv`
- **Divisions**
  - `fightmatch divisions --processed data/processed --features data/features/features.csv`
- **Recommend (single division)**
  - `fightmatch recommend --division "Welterweight" --top 10`
- **Recommend across all divisions**
  - `fightmatch recommend-all --top 5`
- **Demo**
  - `fightmatch demo` (reuses existing `data/processed` + `data/features/features.csv` and runs `recommend-all`).

## Output artifacts

- **Raw data**
  - `data/raw/ufcstats/` — cached HTML (events, fights).
- **Processed dataset**
  - `data/processed/fighters.json`
  - `data/processed/events.json`
  - `data/processed/bouts.json`
  - `data/processed/stats.jsonl`
- **Features**
  - `data/features/features.csv` — per-fighter features (activity, win streaks, finishing, pace, etc.).
- **Reports**
  - `data/reports/<division_slug>.json` — machine-readable per-division report.
  - `data/reports/<division_slug>.md` — Markdown per-division report (top contenders + top matchups + explanations).
  - `data/reports/summary.md` — cross-division summary (all divisions, top 3 contenders, top 1 matchup each).

## Demo

After running the scrape → build-dataset → features steps once, you can generate a full portfolio-ready analytics snapshot with:

```bash
fightmatch demo
```

This will:

- Detect divisions from existing processed data and features.
- Run `recommend-all` across all detected divisions.
- Write JSON + Markdown reports under `data/reports/`, including `summary.md`.

## Data ethics

- **Rate limit**: default 1 request/second with jitter to UFCStats.
- **Caching**: raw HTML cached on disk with a TTL (7 days by default) to avoid unnecessary repeat hits.
- **Retries**: simple backoff on failures; clear, descriptive User-Agent string.
- **No mock data in the pipeline**: tests use minimal fixture HTML only; production runs use real UFCStats data.

## Layout

```text
.
├── pyproject.toml
├── README.md
├── src/fightmatch/
│   ├── cli.py            # CLI entrypoint
│   ├── config.py         # Scrape/matchmaking config
│   ├── cache.py          # Disk cache for HTTP responses
│   ├── scrape/           # UFCStats client, parse, schemas, store
│   ├── data/             # public data API
│   ├── match/            # rank, score, explain
│   └── utils/
├── tests/                # offline, fixture-based tests
└── .github/workflows/ci.yml
```

## Requirements

- Python 3.11 or 3.12
- `requests`, `beautifulsoup4`, `pydantic`

## Testing

This repo requires **Python >= 3.11**. To run tests locally (single source of truth):

```bash
./scripts/test.sh
```

The script:

- Creates a `.venv` with Python 3.11 if missing (default: `/opt/homebrew/bin/python3.11`; set `PYTHON_311` to override).
- Installs the package in editable mode with dev dependencies.
- Runs `pytest -v`.

All tests are fixture-based and do not require network access.
