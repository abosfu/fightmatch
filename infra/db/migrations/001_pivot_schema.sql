-- FightMatch pivot: reproducible dataset + win-probability + matchmaking
-- Postgres schema for time-based feature computation and train/test split.
-- Run against your Postgres (e.g. Supabase SQL Editor or local).

-- Fighters (canonical for pipeline)
CREATE TABLE IF NOT EXISTS pivot_fighters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  weight_class TEXT NOT NULL,
  stance TEXT,
  dob DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fights
CREATE TABLE IF NOT EXISTS pivot_fights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL,
  weight_class TEXT NOT NULL,
  method TEXT,
  round INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- One row per fighter in a fight: fighter_id vs opponent_id
CREATE TABLE IF NOT EXISTS pivot_fight_participants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fight_id UUID NOT NULL REFERENCES pivot_fights(id) ON DELETE CASCADE,
  fighter_id UUID NOT NULL REFERENCES pivot_fighters(id) ON DELETE CASCADE,
  opponent_id UUID NOT NULL REFERENCES pivot_fighters(id) ON DELETE CASCADE,
  is_winner BOOLEAN,
  is_draw BOOLEAN DEFAULT FALSE,
  finish_type TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(fight_id, fighter_id)
);

CREATE INDEX IF NOT EXISTS idx_pivot_fp_fight ON pivot_fight_participants(fight_id);
CREATE INDEX IF NOT EXISTS idx_pivot_fp_fighter ON pivot_fight_participants(fighter_id);
CREATE INDEX IF NOT EXISTS idx_pivot_fights_date ON pivot_fights(date);

-- Feature table: one row per (fight, fighter) with features computed BEFORE the fight (no leakage)
CREATE TABLE IF NOT EXISTS pivot_fighter_fight_features (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fight_id UUID NOT NULL REFERENCES pivot_fights(id) ON DELETE CASCADE,
  fighter_id UUID NOT NULL REFERENCES pivot_fighters(id) ON DELETE CASCADE,
  opponent_id UUID NOT NULL REFERENCES pivot_fighters(id) ON DELETE CASCADE,
  snapshot_date DATE NOT NULL,
  -- activity
  days_since_last_fight INTEGER,
  fights_last_12m INTEGER NOT NULL DEFAULT 0,
  fights_last_24m INTEGER NOT NULL DEFAULT 0,
  -- form
  win_streak INTEGER NOT NULL DEFAULT 0,
  last_n_results_summary NUMERIC,
  -- experience
  total_fights_to_date INTEGER NOT NULL DEFAULT 0,
  -- opponent strength proxy
  opponent_win_rate_to_date NUMERIC,
  opponent_win_streak_to_date INTEGER NOT NULL DEFAULT 0,
  -- finish rate (KO/sub = finish)
  fighter_finish_rate_to_date NUMERIC,
  -- label (outcome of this fight)
  label_win BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(fight_id, fighter_id)
);

CREATE INDEX IF NOT EXISTS idx_pivot_fff_snapshot ON pivot_fighter_fight_features(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_pivot_fff_fighter ON pivot_fighter_fight_features(fighter_id);
