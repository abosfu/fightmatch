# FightMatch

A matchmaking and rankings **decision-support system** for combat sports organizations, focused on internal use rather than fan-facing content.

## What This Project Actually Does

1. **Core problem**
   - Models **constrained, multi-objective decision-making** in UFC-style matchmaking.
   - Helps organizations balance **rankings, competitive fairness, revenue/hype, risk, activity, and division health** when selecting matchups.

2. **Inputs**
   - **Fighter attributes**: rank, champion/contender tier, derived metrics (streaks, finish rate, days since last fight) via DB or mock data.
   - **Recent fight history**: who fought whom recently, outcomes, and time since last matchup.
   - **Policy preset**: `Sporting Merit`, `Business First`, or `Balanced`, each encoding different priorities and constraints.
   - **Weight class context**: division size, champion, ranking distribution.

3. **Outputs**
   - **Ranked list of recommended opponents** for a target fighter.
   - **Composite score** per candidate from a multi-metric scoring model.
   - **Per-metric breakdown** (e.g., competitiveness/fairness, activity, excitement/hype, division health, risk).
   - **Explanation layer**: structured \"why\" reasons and \"risks\" to support human review rather than black-box output.

4. **Decision logic**
   - **Constraints layer** filters out invalid or undesirable matchups first (same fighter, recent rematch, title-eligibility, injuries, extreme rank gaps, long inactivity).
   - **Scoring model** evaluates remaining candidates across multiple metrics and normalizes to a single comparable score.
   - **Policy presets** adjust metric weights and constraint strictness to reflect organizational strategy (sporting vs commercial vs blended).
   - All results are **deterministic and explainable**; there is no opaque ML model in the loop.

5. **Edge cases handled**
   - Missing or partial metrics (falls back to sensible defaults rather than crashing).
   - Large ranking gaps and unranked vs champion scenarios.
   - Inactive or long-layoff fighters.
   - Title-fight eligibility mismatches (e.g., champion vs non-contender) under strict policies.
   - Injured fighters and recent rematches flagged or blocked according to policy.

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

**📖 For detailed step-by-step instructions, see [docs/runbook.md](docs/runbook.md)**

### Quick Start

1. **Create Supabase project** and get credentials
2. **Run migrations**: Apply `supabase/migrations/0001_init.sql` in Supabase SQL Editor
3. **Load seed data**: Apply `supabase/seed.sql` in Supabase SQL Editor
4. **Configure environment**: Create `.env.local` in `apps/web/` with Supabase credentials
5. **Install dependencies**: `npm install` (root) and `cd apps/web && npm install`
6. **Run dev server**: `cd apps/web && npm run dev`

### Health Check

After setup, verify everything works:
- Visit `http://localhost:3000/api/health` - should return `{ "ok": true, "db": "connected", ... }`
- Visit `http://localhost:3000` - should redirect to weight class dashboard

### Development

- **Web app:** `cd apps/web && npm run dev`
- **Tests:** `cd apps/web && npm run test`
- **Build:** `cd apps/web && npm run build`

## Technical Architecture

- **Monorepo** managed with pnpm workspaces:
  - `apps/web`: Next.js App Router UI + API route handlers.
  - `packages/shared`: shared TypeScript types and Zod schemas.
  - `services/etl`: Python ETL for loading/synchronizing source data into Postgres/Supabase.
  - `supabase/`: SQL migrations and seed data for the database.
- **Decision engine**: pure TypeScript module (`apps/web/lib/decision`) that runs entirely in-process and can operate on **mock data or Supabase-backed data** with the same interface.
- **API layer**: Supabase-backed REST-style endpoints implemented as Next.js route handlers, used by the web UI and available for integration.
- **Deterministic scoring**: all metrics and policies are explicit and covered by unit tests (Vitest) to keep behavior stable and auditable.
- **Separation of concerns**: engine logic is independent from data access; switching from mock inputs to Supabase just swaps the data provider, not the scoring or constraint code.

## Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Database:** Supabase (PostgreSQL)
- **ETL:** Python (requests, beautifulsoup4, pandas)
- **Validation:** Zod

## Skills Demonstrated

- Multi-objective scoring systems for real-world tradeoffs.
- Constraint modeling for eligibility and policy enforcement.
- Decision explainability and narrative outputs for analysts.
- Domain modeling in TypeScript with shared types across layers.
- REST API design using Next.js route handlers.
- Database schema and indexing design for Postgres/Supabase.
- Monorepo management with pnpm workspaces.
- Unit testing with Vitest for engine and scoring logic.
- Graceful error handling and empty states in a production-style UI.

