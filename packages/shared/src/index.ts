// Shared types and Zod schemas for FightMatch

import { z } from 'zod';

// Weight Class
export const WeightClassSchema = z.object({
  id: z.string().uuid(),
  slug: z.string(),
  name: z.string(),
  weight_limit_lbs: z.number().nullable(),
  created_at: z.string().datetime().optional(),
  updated_at: z.string().datetime().optional(),
});

export type WeightClass = z.infer<typeof WeightClassSchema>;

// Fighter
export const FighterSchema = z.object({
  id: z.string().uuid(),
  slug: z.string(),
  name: z.string(),
  ufcstats_id: z.string().nullable(),
  date_of_birth: z.string().date().nullable(),
  height_inches: z.number().nullable(),
  reach_inches: z.number().nullable(),
  stance: z.string().nullable(),
  created_at: z.string().datetime().optional(),
  updated_at: z.string().datetime().optional(),
});

export type Fighter = z.infer<typeof FighterSchema>;

// Fighter with Weight Class
export const FighterWithWeightClassSchema = FighterSchema.extend({
  weight_class_id: z.string().uuid(),
  weight_class_slug: z.string(),
  weight_class_name: z.string(),
});

export type FighterWithWeightClass = z.infer<typeof FighterWithWeightClassSchema>;

// Fighter Metrics
export const FighterMetricsSchema = z.object({
  id: z.string().uuid(),
  fighter_id: z.string().uuid(),
  weight_class_id: z.string().uuid(),
  last_fight_date: z.string().date().nullable(),
  days_since_fight: z.number().nullable(),
  win_streak: z.number().default(0),
  loss_streak: z.number().default(0),
  finish_rate: z.number().nullable(),
  total_fights: z.number().default(0),
  wins: z.number().default(0),
  losses: z.number().default(0),
  draws: z.number().default(0),
  no_contests: z.number().default(0),
  avg_opponent_strength: z.number().nullable(),
  computed_at: z.string().datetime().optional(),
});

export type FighterMetrics = z.infer<typeof FighterMetricsSchema>;

// Fight
export const FightSchema = z.object({
  id: z.string().uuid(),
  event_id: z.string().uuid().nullable(),
  date: z.string().date(),
  weight_class_id: z.string().uuid().nullable(),
  result_type: z.string().nullable(),
  result_method: z.string().nullable(),
  result_round: z.number().nullable(),
  result_time: z.string().nullable(),
  ufcstats_id: z.string().nullable(),
});

export type Fight = z.infer<typeof FightSchema>;

// Fight Participant
export const FightParticipantSchema = z.object({
  id: z.string().uuid(),
  fight_id: z.string().uuid(),
  fighter_id: z.string().uuid(),
  is_winner: z.boolean().nullable(),
  is_champion: z.boolean().default(false),
  weight_lbs: z.number().nullable(),
});

export type FightParticipant = z.infer<typeof FightParticipantSchema>;

// Fight with Participants
export const FightWithParticipantsSchema = FightSchema.extend({
  participants: z.array(
    FightParticipantSchema.extend({
      fighter: FighterSchema,
    })
  ),
});

export type FightWithParticipants = z.infer<typeof FightWithParticipantsSchema>;

// Ranking Entry
export const RankingEntrySchema = z.object({
  id: z.string().uuid(),
  ranking_id: z.string().uuid(),
  fighter_id: z.string().uuid(),
  rank: z.number(),
  tier: z.string().nullable(),
});

export type RankingEntry = z.infer<typeof RankingEntrySchema>;

// Ranking Entry with Fighter
export const RankingEntryWithFighterSchema = RankingEntrySchema.extend({
  fighter: FighterSchema,
  metrics: FighterMetricsSchema.nullable(),
});

export type RankingEntryWithFighter = z.infer<typeof RankingEntryWithFighterSchema>;

// Matchup Score Components
export const MatchupScoreComponentsSchema = z.object({
  competitiveness: z.number(),
  activity: z.number(),
  excitement: z.number(),
  risk: z.number(),
});

export type MatchupScoreComponents = z.infer<typeof MatchupScoreComponentsSchema>;

// Matchup Score Result
export const MatchupScoreResultSchema = z.object({
  total: z.number(),
  components: MatchupScoreComponentsSchema,
  explanation: z.object({
    why: z.array(z.string()),
    risks: z.array(z.string()),
  }),
});

export type MatchupScoreResult = z.infer<typeof MatchupScoreResultSchema>;

// Recommendation Result
export const RecommendationResultSchema = z.object({
  opponent: FighterSchema.extend({
    metrics: FighterMetricsSchema.nullable(),
    rank: z.number().nullable(),
    tier: z.string().nullable(),
  }),
  score: MatchupScoreResultSchema,
});

export type RecommendationResult = z.infer<typeof RecommendationResultSchema>;

