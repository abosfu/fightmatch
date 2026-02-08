# FightMatch Architecture

## Overview

FightMatch is a UFC matchmaking + rankings decision support tool built as a monorepo with a Next.js web application and a Python ETL service.

## Project Structure

```
fightmatch/
├── apps/
│   └── web/                    # Next.js App Router application
│       ├── app/                 # App Router pages and API routes
│       ├── lib/                 # Business logic and utilities
│       │   ├── db/             # Database access layer
│       │   └── scoring/        # Matchup scoring logic
│       └── ...
├── services/
│   └── etl/                     # Python ETL service
│       └── scripts/             # ETL scripts
├── packages/
│   └── shared/                  # Shared TypeScript types and Zod schemas
├── supabase/
│   ├── migrations/              # Database migrations
│   └── seed.sql                 # Seed data
└── docs/                        # Documentation
```

## Data Flow

### 1. Data Ingestion (ETL)

**Current (MVP):**
- Seed data loaded via `services/etl/scripts/etl_load_seed.py`
- CSV import via `services/etl/scripts/etl_from_csv.py`

**Future:**
- Scrape UFCStats.com using `requests` and `beautifulsoup4`
- Transform and load into Supabase PostgreSQL
- Update `fighter_metrics` table via recomputation endpoint

### 2. Database Layer

**Schema:**
- Core entities: `fighters`, `weight_classes`, `fights`, `events`
- Associations: `fighter_weight_class`, `fight_participants`
- Rankings: `rankings`, `ranking_entries`
- Metrics: `fighter_metrics` (computed/derived)
- Recommendations: `recommendation_runs`, `recommendation_results` (for caching)

**Access Pattern:**
- Server-side: `lib/db/supabaseServer.ts` (uses service role key)
- Client-side: `lib/db/supabaseBrowser.ts` (uses anon key)
- Query functions: `lib/db/queries.ts` (typed, reusable queries)

### 3. Scoring Model

**Location:** `apps/web/lib/scoring/matchup.ts`

**Function:** `scoreMatchup(fighter, opponent, context)`

**Components:**
1. **Competitiveness** (0-1)
   - Rank proximity
   - Tier matching
   - Opponent strength proximity (win rate similarity)

2. **Activity** (0-1)
   - Days since fight (both fighters)
   - Activity compatibility (both should be similarly active)

3. **Excitement** (0-1)
   - Average finish rate
   - Style proxy (both high finishers = exciting)
   - Streak bonus

4. **Risk** (0-1, inverted)
   - Rematch penalty (if they've fought before)
   - Mismatch penalty (large rank gap)
   - Champion vs unranked penalty

**Output:**
- `total`: Average of all components
- `components`: Individual scores
- `explanation`: `{ why: string[], risks: string[] }`

**Testing:**
- Unit tests in `lib/scoring/matchup.test.ts` (Vitest)
- 5 test cases covering competitive matchups, ranking gaps, finish rates, inactivity, and missing metrics

### 4. API Layer

**Next.js Route Handlers** (App Router):

- `GET /api/weight-classes` - List all weight classes
- `GET /api/fighters?weightClassId=&search=` - List fighters with filters
- `GET /api/fighters/[id]` - Get fighter by ID/slug
- `GET /api/fighters/[id]/fights?limit=` - Get fighter's recent fights
- `GET /api/recommendations?fighterId=&weightClassId=` - Generate recommendations
- `POST /api/admin/rankings` - Upsert ranking entries (admin only)
- `POST /api/admin/recompute-metrics` - Recompute fighter metrics (stub)

### 5. UI Layer

**Pages:**

1. `/` - Redirects to `/wc/lightweight`
2. `/wc/[slug]` - Weight class dashboard (server component)
   - Shows table of fighters with metrics
   - Fetches from DB via `getRankingEntriesWithFighters()`
3. `/fighters` - Fighters directory (server component)
   - Search and filter by weight class
4. `/fighters/[slug]` - Fighter profile (server component)
   - Header with fighter info
   - Derived metrics display
   - Recent fights list
   - "Recommend opponents" button
5. `/recommend` - Recommender page (client component)
   - Fighter autocomplete search
   - Calls `/api/recommendations`
   - Renders top 5 with score breakdown bars
   - Shows "why" and "risks" explanations
6. `/admin/rankings` - Admin rankings editor (client component)
   - MVP: Simple table editor
   - Protected via `ADMIN_SECRET` env var
   - Structured for Supabase RLS later

## Key Design Decisions

### Monorepo Structure
- Shared types in `packages/shared` ensure type safety across web app and future services
- ETL service is separate Python package for independent deployment

### Database Access
- Server-side uses service role key for admin operations
- Client-side uses anon key (future: RLS policies)
- Query functions abstract Supabase client details

### Scoring Model
- Pure TypeScript function (no database dependencies)
- Easy to test and iterate
- Can be swapped for ML model later

### Admin Access (MVP)
- Simple `ADMIN_SECRET` bearer token
- In production, use Supabase Auth + RLS policies
- Code structured to support RLS migration

## Future Enhancements

### Data Source
- Replace seed/CSV with UFCStats scraper
- Implement `etl_scrape_ufcstats.py`
- Schedule periodic updates

### Scoring
- Add more factors (injury history, style matchups)
- Consider ML model for score prediction
- A/B test different scoring algorithms

### Authentication
- Migrate admin routes to Supabase Auth
- Implement RLS policies
- Add user roles (admin, analyst, viewer)

### Metrics Computation
- Implement `/api/admin/recompute-metrics` endpoint
- Schedule automatic recomputation
- Add metrics versioning/history

### Caching
- Cache recommendation results in `recommendation_results` table
- Invalidate on new fights/rankings
- Add TTL for stale recommendations

## Deployment

### Web App
- Deploy to Vercel/Netlify
- Set environment variables (Supabase keys, admin secret)
- Run migrations via Supabase dashboard or CLI

### ETL Service
- Deploy as scheduled job (GitHub Actions, AWS Lambda, etc.)
- Run on schedule to update data
- Monitor for errors

### Database
- Supabase hosted PostgreSQL
- Run migrations via Supabase CLI or dashboard
- Backup and restore via Supabase dashboard

