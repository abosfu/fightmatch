# FightMatch Runbook

Step-by-step instructions to get FightMatch running end-to-end with Supabase.

## Prerequisites

- Node.js 18+ and npm installed
- Python 3.9+ (optional, for ETL)
- Supabase account (free tier works)

## Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in:
   - **Name**: `fightmatch` (or your choice)
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free tier is fine for MVP
4. Click "Create new project"
5. Wait 2-3 minutes for project to be provisioned

## Step 2: Get Supabase Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. You'll need these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)
   - **service_role key** (starts with `eyJ...`, keep this secret!)

3. Also note your database connection string:
   - Go to **Settings** → **Database**
   - Under "Connection string", select "URI"
   - Copy the connection string (format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`)

## Step 3: Run Database Migrations

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Open `supabase/migrations/0001_init.sql` from this repo
4. Copy the entire contents
5. Paste into the SQL Editor
6. Click "Run" (or press Cmd/Ctrl + Enter)
7. Wait for success message - you should see "Success. No rows returned"

**Verify migration:**
- In the left sidebar, click "Table Editor"
- You should see tables: `fighters`, `weight_classes`, `fights`, `events`, `rankings`, etc.

## Step 4: Load Seed Data

1. In Supabase dashboard, go to **SQL Editor** again
2. Click "New query"
3. Open `supabase/seed.sql` from this repo
4. Copy the entire contents
5. Paste into the SQL Editor
6. Click "Run"
7. Wait for success - you may see some "Skipped (already exists)" messages, which is fine

**Verify seed data:**
- Go to **Table Editor** → `fighters`
- You should see 10 fighters (Islam Makhachev, Charles Oliveira, etc.)
- Go to `weight_classes` - should see Lightweight, Welterweight, Middleweight
- Go to `rankings` - should see ranking entries

## Step 5: Configure Environment Variables

1. In the repo root, create `.env.local` (or copy from `.env.example` if it exists):

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Admin Access (MVP - simple secret for admin routes)
ADMIN_SECRET=your-secret-key-here-change-this

# Database (for ETL - optional)
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

2. Replace:
   - `NEXT_PUBLIC_SUPABASE_URL` with your Project URL from Step 2
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` with your anon/public key
   - `SUPABASE_SERVICE_ROLE_KEY` with your service_role key
   - `ADMIN_SECRET` with a random secret (e.g., `openssl rand -hex 32`)
   - `DATABASE_URL` with your connection string (if using ETL)

**Important:** Never commit `.env.local` to git!

## Step 6: Install Dependencies

```bash
# From repo root
npm install

# Install web app dependencies
cd apps/web
npm install

# Install shared package dependencies
cd ../../packages/shared
npm install
```

## Step 7: Run Development Server

```bash
# From repo root
cd apps/web
npm run dev
```

The app should start at `http://localhost:3000`

## Step 8: Sanity Check Routes/Pages

### Health Check
- Visit `http://localhost:3000/api/health`
- Should return: `{ "ok": true, "db": "connected", "counts": { "fighters": 10, "fights": 4, "events": 4 } }`

### Pages to Test

1. **Homepage** (`/`)
   - Should redirect to `/wc/lightweight`

2. **Weight Class Dashboard** (`/wc/lightweight`)
   - Should show table with 5 fighters (Islam Makhachev, Charles Oliveira, etc.)
   - Check: names, ranks, tiers, metrics display correctly

3. **Fighters Directory** (`/fighters`)
   - Should show list of fighters
   - Test search: type "Islam" - should filter
   - Test weight class filter: switch between Lightweight/Welterweight

4. **Fighter Profile** (`/fighters/islam-makhachev`)
   - Should show fighter details, metrics, recent fights
   - Click "Recommend Opponents" button

5. **Recommendations** (`/recommend`)
   - Search for "Islam Makhachev"
   - Click "Get Recommendations"
   - Should show top 5 opponents with score breakdowns

6. **Admin Rankings** (`/admin/rankings`)
   - Enter your `ADMIN_SECRET` from `.env.local`
   - Should show rankings editor (MVP version)

## Troubleshooting

### "Missing Supabase environment variables"
- Check `.env.local` exists in `apps/web/` directory
- Verify all three Supabase keys are set
- Restart dev server after changing `.env.local`

### "Failed to fetch" errors
- Check Supabase project is active (not paused)
- Verify `NEXT_PUBLIC_SUPABASE_URL` is correct (no trailing slash)
- Check browser console for CORS errors

### Database connection errors
- Verify migrations ran successfully
- Check seed data loaded (use Table Editor in Supabase)
- Ensure `SUPABASE_SERVICE_ROLE_KEY` is correct (not anon key)

### Empty pages / "No data found"
- Run seed SQL again (it's idempotent)
- Check Table Editor in Supabase to verify data exists
- Check browser console for errors

### Admin page authentication fails
- Verify `ADMIN_SECRET` in `.env.local` matches what you're entering
- Check server logs for "Unauthorized" errors
- Ensure `.env.local` is in `apps/web/` directory (not repo root)

## Next Steps

Once everything works:
- Review `docs/architecture.md` for system overview
- Check `services/etl/README.md` for data loading options
- Consider setting up automated ETL for real UFC data

## Production Deployment

For production:
1. Set up Supabase production project
2. Run migrations and seed
3. Configure environment variables in hosting platform (Vercel, etc.)
4. Enable Row Level Security (RLS) policies
5. Replace `ADMIN_SECRET` with proper Supabase Auth

