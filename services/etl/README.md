# FightMatch ETL Service

Python service for loading and transforming UFC data into the FightMatch database.

## Setup

1. **Install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

2. **Set environment variables:**
   Create a `.env` file in this directory:
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

   Or use your Supabase connection string:
   ```
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

## Usage

### Load Seed Data

Loads the sample seed dataset into the database:

```bash
python scripts/etl_load_seed.py
```

This script:
- Connects to the database using `DATABASE_URL`
- Executes SQL from `supabase/seed.sql` (or equivalent seed data)
- Can be run multiple times (idempotent with `ON CONFLICT` handling)

### Load from CSV

If you have CSV files with fighter/fight data:

```bash
python scripts/etl_from_csv.py --fighters fighters.csv --fights fights.csv --participants participants.csv
```

## Future: UFCStats Scraping

The ETL service is structured to support scraping from UFCStats.com. To implement:

1. Create `scripts/etl_scrape_ufcstats.py`
2. Use `requests` and `beautifulsoup4` to scrape:
   - Fighter profiles
   - Event listings
   - Fight results
   - Rankings
3. Transform and load into database using the same patterns as CSV loader

**Note:** Be respectful of rate limits and robots.txt when scraping.

## Database Schema

See `supabase/migrations/0001_init.sql` for the full schema.

Key tables:
- `fighters` - Fighter profiles
- `weight_classes` - Weight class definitions
- `fights` - Fight records
- `fight_participants` - Fighter participation in fights
- `rankings` - Ranking snapshots
- `fighter_metrics` - Computed metrics

