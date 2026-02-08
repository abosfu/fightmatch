-- FightMatch Database Schema
-- Supabase PostgreSQL Migration

-- Weight Classes
CREATE TABLE IF NOT EXISTS weight_classes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  weight_limit_lbs NUMERIC,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fighters
CREATE TABLE IF NOT EXISTS fighters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  ufcstats_id TEXT UNIQUE,
  date_of_birth DATE,
  height_inches INTEGER,
  reach_inches INTEGER,
  stance TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fighter-Weight Class Association (many-to-many)
CREATE TABLE IF NOT EXISTS fighter_weight_class (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fighter_id UUID NOT NULL REFERENCES fighters(id) ON DELETE CASCADE,
  weight_class_id UUID NOT NULL REFERENCES weight_classes(id) ON DELETE CASCADE,
  is_primary BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(fighter_id, weight_class_id)
);

-- Events
CREATE TABLE IF NOT EXISTS events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  date DATE NOT NULL,
  location TEXT,
  ufcstats_id TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fights
CREATE TABLE IF NOT EXISTS fights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID REFERENCES events(id) ON DELETE SET NULL,
  date DATE NOT NULL,
  weight_class_id UUID REFERENCES weight_classes(id) ON DELETE SET NULL,
  result_type TEXT, -- 'KO/TKO', 'Submission', 'Decision', etc.
  result_method TEXT,
  result_round INTEGER,
  result_time TEXT,
  ufcstats_id TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fight Participants
CREATE TABLE IF NOT EXISTS fight_participants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fight_id UUID NOT NULL REFERENCES fights(id) ON DELETE CASCADE,
  fighter_id UUID NOT NULL REFERENCES fighters(id) ON DELETE CASCADE,
  is_winner BOOLEAN,
  is_champion BOOLEAN DEFAULT FALSE,
  weight_lbs NUMERIC,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(fight_id, fighter_id)
);

-- Rankings (snapshots)
CREATE TABLE IF NOT EXISTS rankings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  weight_class_id UUID NOT NULL REFERENCES weight_classes(id) ON DELETE CASCADE,
  snapshot_date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(weight_class_id, snapshot_date)
);

-- Ranking Entries
CREATE TABLE IF NOT EXISTS ranking_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ranking_id UUID NOT NULL REFERENCES rankings(id) ON DELETE CASCADE,
  fighter_id UUID NOT NULL REFERENCES fighters(id) ON DELETE CASCADE,
  rank INTEGER NOT NULL,
  tier TEXT, -- 'Champion', 'Contender', 'Prospect', etc.
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(ranking_id, fighter_id),
  UNIQUE(ranking_id, rank)
);

-- Fighter Metrics (derived/computed)
CREATE TABLE IF NOT EXISTS fighter_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fighter_id UUID NOT NULL REFERENCES fighters(id) ON DELETE CASCADE,
  weight_class_id UUID NOT NULL REFERENCES weight_classes(id) ON DELETE CASCADE,
  last_fight_date DATE,
  days_since_fight INTEGER,
  win_streak INTEGER DEFAULT 0,
  loss_streak INTEGER DEFAULT 0,
  finish_rate NUMERIC, -- percentage of wins by finish
  total_fights INTEGER DEFAULT 0,
  wins INTEGER DEFAULT 0,
  losses INTEGER DEFAULT 0,
  draws INTEGER DEFAULT 0,
  no_contests INTEGER DEFAULT 0,
  avg_opponent_strength NUMERIC,
  computed_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(fighter_id, weight_class_id)
);

-- Recommendation Runs (for tracking)
CREATE TABLE IF NOT EXISTS recommendation_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fighter_id UUID NOT NULL REFERENCES fighters(id) ON DELETE CASCADE,
  weight_class_id UUID NOT NULL REFERENCES weight_classes(id) ON DELETE CASCADE,
  run_at TIMESTAMPTZ DEFAULT NOW(),
  context JSONB
);

-- Recommendation Results (cached recommendations)
CREATE TABLE IF NOT EXISTS recommendation_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID REFERENCES recommendation_runs(id) ON DELETE CASCADE,
  fighter_id UUID NOT NULL REFERENCES fighters(id) ON DELETE CASCADE,
  opponent_id UUID NOT NULL REFERENCES fighters(id) ON DELETE CASCADE,
  total_score NUMERIC NOT NULL,
  competitiveness_score NUMERIC,
  activity_score NUMERIC,
  excitement_score NUMERIC,
  risk_score NUMERIC,
  explanation JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_fighters_slug ON fighters(slug);
CREATE INDEX IF NOT EXISTS idx_fighters_ufcstats_id ON fighters(ufcstats_id);
CREATE INDEX IF NOT EXISTS idx_weight_classes_slug ON weight_classes(slug);
CREATE INDEX IF NOT EXISTS idx_fighter_weight_class_fighter ON fighter_weight_class(fighter_id);
CREATE INDEX IF NOT EXISTS idx_fighter_weight_class_wc ON fighter_weight_class(weight_class_id);
CREATE INDEX IF NOT EXISTS idx_fights_event ON fights(event_id);
CREATE INDEX IF NOT EXISTS idx_fights_date ON fights(date);
CREATE INDEX IF NOT EXISTS idx_fight_participants_fight ON fight_participants(fight_id);
CREATE INDEX IF NOT EXISTS idx_fight_participants_fighter ON fight_participants(fighter_id);
CREATE INDEX IF NOT EXISTS idx_rankings_weight_class ON rankings(weight_class_id);
CREATE INDEX IF NOT EXISTS idx_ranking_entries_ranking ON ranking_entries(ranking_id);
CREATE INDEX IF NOT EXISTS idx_ranking_entries_fighter ON ranking_entries(fighter_id);
CREATE INDEX IF NOT EXISTS idx_fighter_metrics_fighter ON fighter_metrics(fighter_id);
CREATE INDEX IF NOT EXISTS idx_fighter_metrics_weight_class ON fighter_metrics(weight_class_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_results_fighter ON recommendation_results(fighter_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_results_opponent ON recommendation_results(opponent_id);

