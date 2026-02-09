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

## Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Database:** Supabase (PostgreSQL)
- **ETL:** Python (requests, beautifulsoup4, pandas)
- **Validation:** Zod

