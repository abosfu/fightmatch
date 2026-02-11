/**
 * Domain model for Decision Support Engine
 * Pure TypeScript types - no Supabase dependencies
 */

export interface Fighter {
  id: string
  name: string
  rank: number
  lastFightDate: Date | null
  popularityScore: number // 0-100, proxy for hype/revenue
  isChampion: boolean
  isInjured: boolean
  // TODO: Replace with Supabase fighter data
  // - Get from fighters table
  // - Include metrics from fighter_metrics table
}

export interface DivisionContext {
  weightClassId: string
  weightClassName: string
  totalFighters: number
  championId: string | null
  // TODO: Replace with Supabase division data
  // - Get from weight_classes table
  // - Include ranking snapshot from rankings table
}

export interface MatchupCandidate {
  fighter: Fighter
  totalScore: number
  breakdown: MatchupScoreBreakdown
  violations: ConstraintViolation[]
  explanation: string
}

export interface MatchupScoreBreakdown {
  fairness: number // 0-1, penalize large rank gaps
  divisionHealth: number // 0-1, reward fights that reduce logjams
  risk: number // 0-1, penalize uncertainty (inverted - higher is better)
  hype: number // 0-1, reward popular matchups
  activity: number // 0-1, reward active fighters
}

export interface ConstraintViolation {
  type: ConstraintType
  reason: string
  severity: 'blocking' | 'warning'
}

export type ConstraintType =
  | 'same_fighter'
  | 'recent_matchup'
  | 'title_fight_eligibility'
  | 'rank_gap_too_high'
  | 'injured_fighter'
  | 'inactive_too_long'

export interface Policy {
  name: string
  description: string
  weights: {
    fairness: number
    divisionHealth: number
    risk: number
    hype: number
    activity: number
  }
  constraints: {
    allowRecentMatchup: boolean // If false, block fighters who fought recently
    maxRankGap: number | null // null = no limit
    requireTitleEligibility: boolean // If true, only contenders can fight champion
    blockInjured: boolean
    maxDaysInactive: number | null // null = no limit
  }
}

export interface RecommendationResult {
  targetFighter: Fighter
  candidates: MatchupCandidate[]
  blocked: MatchupCandidate[]
  policy: Policy
  context: DivisionContext
}

