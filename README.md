# FightMatch

A UFC matchmaking + rankings decision support tool (internal tool).

## Project Structure

```
fightmatch/
├── apps/
│   └── web/              # Next.js App Router application
├── services/
│   └── etl/              # Python ETL service for data loading
├── packages/
│   └── shared/           # Shared TypeScript types and Zod schemas
├── docs/                 # Architecture and product documentation
└── supabase/
    └── migrations/       # Database migrations
```

## How to Run Locally

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+ (for ETL service)
- Supabase account and project (or local Supabase instance)

### Setup

1. **Clone and install dependencies:**
   ```bash
   npm install
   cd apps/web && npm install
   cd ../../packages/shared && npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

3. **Set up database:**
   ```bash
   # Run migrations (via Supabase CLI or dashboard)
   # Or apply supabase/migrations/0001_init.sql manually
   
   # Load seed data
   # Apply supabase/seed.sql via Supabase SQL editor or CLI
   ```

4. **Run the web app:**
   ```bash
   npm run dev
   # Or: cd apps/web && npm run dev
   ```
   The app will be available at http://localhost:3000

5. **Run ETL (optional, for loading data):**
   ```bash
   cd services/etl
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   python scripts/etl_load_seed.py
   ```

### Development

- **Web app:** `cd apps/web && npm run dev`
- **Tests:** `cd apps/web && npm run test`
- **Build:** `cd apps/web && npm run build`

## Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Database:** Supabase (PostgreSQL)
- **ETL:** Python (requests, beautifulsoup4, pandas)
- **Validation:** Zod

