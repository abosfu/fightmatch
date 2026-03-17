# FightMatch

**FightMatch** is a CLI-first UFC matchmaking and analytics tool. It ingests real fight data from `ufcstats.com`, builds a structured dataset, ranks fighters within each division, and recommends matchups with short, human-readable explanations.

## What FightMatch is

- **Data-backed decision support** for UFC matchmaking: rankings, contender clarity, and style-test ideas.
- **Division-aware**: works across all UFC divisions detected in the processed dataset.
- **Artifact-first**: produces machine-readable JSON and human-readable Markdown reports, suitable for portfolios and lightweight analytics workflows.

## System Capabilities

- **Sports data ingestion** — rate-limited HTTP scraping of a live third-party source with disk-based caching, retry logic, and configurable TTL; no external data libraries required.
- **Structured dataset construction** — HTML parsing pipeline that normalises semi-structured event, bout, and per-fight statistics pages into clean, queryable JSON and JSONL artefacts.
- **Fighter performance analytics** — engineered feature set covering activity decay, recent form, striking and grappling efficiency, finish rate, and opponent quality; all metrics are interpretable and deterministic.
- **Fighter rating engine** — composite 0–10 scoring model with explicitly weighted, normalised components; produces per-division rankings and percentile positions.
- **Matchup simulation** — heuristic win-probability proxy derived from a logistic function over fighter rating deltas, paired with competitive balance, style contrast, and divisional rank-impact scores.
- **Promoter decision scoring** — configurable multi-factor model that weights competitive balance, divisional relevance, activity readiness, rematch freshness, and style interest to rank candidate matchups from a business perspective.
- **Explainable outputs** — every recommendation is accompanied by human-readable factor signals; no black-box scoring.
- **Automated report generation** — CLI pipeline writes structured JSON and Markdown reports for each division and a cross-division summary, suitable for downstream analytics workflows or portfolio review.

## Why it exists

- To demonstrate a **production-like analytics pipeline** on real-world sports data (scraping → dataset → features → rankings → recommendations).
- To provide a **clean, recruiter-friendly codebase**: minimal dependencies, offline tests, and a clear end-to-end story.
- To explore **matchmaking heuristics** (activity, rank gaps, rematch avoidance, style clashes) in a way that’s transparent and configurable.

## System Architecture

```
  ┌─────────────────────────────────────────┐
  │             UFCStats.com                │
  │   (event results, fight stats, bouts)   │
  └────────────────────┬────────────────────┘
                       │ HTTP (rate-limited, retried)
                       ▼
  ┌─────────────────────────────────────────┐
  │           Scraping Layer                │
  │   fightmatch scrape --since YYYY-MM-DD  │
  └────────────────────┬────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────┐
  │         Raw HTML Cache                  │
  │   data/raw/ufcstats/  (TTL: 7 days)    │
  └────────────────────┬────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────┐
  │          Dataset Builder                │
  │   fightmatch build-dataset              │
  └────────────────────┬────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────┐
  │       Structured Datasets               │
  │   fighters.json  ·  events.json         │
  │   bouts.json     ·  stats.jsonl         │
  └────────────────────┬────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────┐
  │         Feature Engineering             │
  │   fightmatch features                   │
  │                                         │
  │   activity · form · efficiency          │
  │   finish rate · opponent quality        │
  └────────────────────┬────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────┐
  │          Analytics Engine               │
  │   Fighter Rating  (0–10)                │
  │   Fighter Profile · Style Archetype     │
  │   Division Rankings                     │
  └──────────┬──────────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────────┐
  │       Matchup Simulation Engine         │
  │   Win probability proxy (logistic)      │
  │   Competitiveness · Style contrast      │
  │   Rank impact                           │
  └──────────┬──────────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────────┐
  │        Promoter Decision Model          │
  │   Competitiveness  30%                  │
  │   Divisional relevance  20%             │
  │   Activity readiness  20%               │
  │   Freshness · Style interest  25%       │
  │   Fan interest proxy  5%                │
  └──────────┬──────────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────────┐
  │     Decision-Support Outputs            │
  │   data/reports/<division>.json          │
  │   data/reports/<division>.md            │
  │   data/reports/summary.md              │
  └─────────────────────────────────────────┘
```

The pipeline begins by scraping real fight data from UFCStats into a local HTML cache, then parses that cache into normalized JSON datasets (fighters, events, bouts, per-fight statistics). Feature engineering runs over the structured data to produce per-fighter metrics — activity decay, recent form, striking and grappling efficiency, finish rate, and opponent quality. The analytics engine converts those metrics into a composite 0–10 fighter rating and a rich style profile for each fighter, which powers division rankings. Finally, the matchup simulation engine evaluates all candidate pairings by computing win probability, competitive balance, and style contrast, while the promoter decision model applies configurable business weights to surface the highest-value fights as JSON and Markdown reports.

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

After running the scrape → build-dataset → features steps once, generate a full analytics snapshot:

```bash
fightmatch demo
```

This detects divisions from your local processed data and features, runs `recommend-all` across all detected divisions, and writes JSON + Markdown reports under `data/reports/`.

`fightmatch demo` requires real local data. If the processed directory or features file is missing or empty, it will tell you exactly which step to run next.

## Example outputs

The [`examples/`](examples/) directory contains annotated templates that mirror the exact structure of every report FightMatch produces. Each file uses `[placeholder]` tokens in place of computed values so the format is clear without requiring a live data run.

| File | Corresponding CLI command |
|------|--------------------------|
| [`examples/fighter_profile_example.md`](examples/fighter_profile_example.md) | `fightmatch fighter-profile` |
| [`examples/matchup_simulation_example.md`](examples/matchup_simulation_example.md) | `fightmatch simulate` |
| [`examples/division_recommendations_example.md`](examples/division_recommendations_example.md) | `fightmatch recommend` / `recommend-all` |

Actual reports with computed values are written to `data/reports/` when you run the pipeline against real UFC data.

## Data availability

FightMatch operates exclusively on real UFC-derived data. It does not ship any bundled or fabricated fighter rows.

| Situation | Behaviour |
|-----------|-----------|
| UFCStats reachable | `fightmatch scrape` downloads and caches raw HTML |
| UFCStats unreachable | `scrape` exits cleanly; tells you whether cached HTML is available to continue from |
| Cached HTML present, no network needed | `build-dataset` + `features` + `demo` work fully offline from the cache |
| No data at all | Commands fail with a precise message and the exact command to run next |

The scrape cache (`data/raw/`) is gitignored and lives on your local machine. Once you have scraped and built a processed dataset, all analysis commands work without any further network access.

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
│   ├── cli.py              # CLI entrypoint (all commands)
│   ├── config.py           # Scrape/matchmaking config
│   ├── cache.py            # Disk cache for HTTP responses
│   ├── scrape/             # UFCStats client, parse, schemas, store
│   ├── data/               # public data API
│   ├── match/              # rank, score, explain
│   ├── analytics/          # fighter rating engine + analytics profile
│   ├── engine/             # matchup simulation + promoter decision scoring
│   └── utils/
├── tests/                  # offline, fixture-based tests (68 tests)
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
