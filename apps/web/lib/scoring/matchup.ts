import type {
  Fighter,
  FighterMetrics,
  MatchupScoreResult,
  MatchupScoreComponents,
} from '@fightmatch/shared'

interface MatchupContext {
  weightClassId: string
  allFightersInClass: number
}

interface FighterWithMetrics extends Fighter {
  metrics: FighterMetrics | null
  rank: number | null
  tier: string | null
}

export function scoreMatchup(
  fighter: FighterWithMetrics,
  opponent: FighterWithMetrics,
  context: MatchupContext
): MatchupScoreResult {
  const components: MatchupScoreComponents = {
    competitiveness: scoreCompetitiveness(fighter, opponent, context),
    activity: scoreActivity(fighter, opponent),
    excitement: scoreExcitement(fighter, opponent),
    risk: scoreRisk(fighter, opponent),
  }

  const total = Object.values(components).reduce((sum, val) => sum + val, 0) / Object.keys(components).length

  const explanation = {
    why: generateWhy(fighter, opponent, components),
    risks: generateRisks(fighter, opponent, components),
  }

  return {
    total: Math.round(total * 100) / 100,
    components,
    explanation,
  }
}

function scoreCompetitiveness(
  fighter: FighterWithMetrics,
  opponent: FighterWithMetrics,
  context: MatchupContext
): number {
  let score = 0.5 // Base score

  // Rank proximity (closer ranks = more competitive)
  if (fighter.rank !== null && opponent.rank !== null) {
    const rankDiff = Math.abs(fighter.rank - opponent.rank)
    const maxRank = context.allFightersInClass || 15
    const proximityScore = 1 - Math.min(rankDiff / maxRank, 1)
    score = score * 0.6 + proximityScore * 0.4
  }

  // Tier matching
  if (fighter.tier && opponent.tier) {
    if (fighter.tier === opponent.tier) {
      score += 0.2
    } else if (
      (fighter.tier === 'Champion' && opponent.tier === 'Contender') ||
      (fighter.tier === 'Contender' && opponent.tier === 'Champion')
    ) {
      score += 0.15
    }
  }

  // Opponent strength proximity (using win rates as proxy)
  const fighterWinRate = fighter.metrics
    ? fighter.metrics.wins / Math.max(fighter.metrics.total_fights, 1)
    : 0.5
  const opponentWinRate = opponent.metrics
    ? opponent.metrics.wins / Math.max(opponent.metrics.total_fights, 1)
    : 0.5

  const winRateDiff = Math.abs(fighterWinRate - opponentWinRate)
  score += (1 - winRateDiff) * 0.2

  return Math.min(Math.max(score, 0), 1)
}

function scoreActivity(fighter: FighterWithMetrics, opponent: FighterWithMetrics): number {
  let score = 0.5

  // Days since fight (both should be active)
  const fighterDays = fighter.metrics?.days_since_fight ?? 365
  const opponentDays = opponent.metrics?.days_since_fight ?? 365

  // Ideal: both fought within last 6 months (180 days)
  const fighterActivity = Math.max(0, 1 - fighterDays / 365)
  const opponentActivity = Math.max(0, 1 - opponentDays / 365)

  // Compatibility: both should be similarly active
  const activityDiff = Math.abs(fighterActivity - opponentActivity)
  const compatibility = 1 - activityDiff

  score = (fighterActivity + opponentActivity) / 2 * 0.6 + compatibility * 0.4

  return Math.min(Math.max(score, 0), 1)
}

function scoreExcitement(fighter: FighterWithMetrics, opponent: FighterWithMetrics): number {
  let score = 0.5

  const fighterFinishRate = fighter.metrics?.finish_rate ?? 0.5
  const opponentFinishRate = opponent.metrics?.finish_rate ?? 0.5

  // Higher finish rates = more exciting
  const avgFinishRate = (fighterFinishRate + opponentFinishRate) / 2
  score = avgFinishRate * 0.7

  // Style proxy: if both have high finish rates, it's exciting
  if (fighterFinishRate > 0.7 && opponentFinishRate > 0.7) {
    score += 0.2
  }

  // Streak bonus
  const fighterStreak = fighter.metrics?.win_streak ?? 0
  const opponentStreak = opponent.metrics?.win_streak ?? 0
  if (fighterStreak >= 3 || opponentStreak >= 3) {
    score += 0.1
  }

  return Math.min(Math.max(score, 0), 1)
}

function scoreRisk(fighter: FighterWithMetrics, opponent: FighterWithMetrics): number {
  // Risk is inverted: lower risk = higher score
  let risk = 0.5

  // Rematch penalty (if they've fought before - simplified check)
  // In real implementation, check fight history
  // For now, we'll skip this check

  // Mismatch penalty
  if (fighter.rank !== null && opponent.rank !== null) {
    const rankDiff = Math.abs(fighter.rank - opponent.rank)
    if (rankDiff > 5) {
      risk += 0.3 // High rank difference = higher risk
    }
  }

  // Champion vs unranked = high risk
  if (
    (fighter.tier === 'Champion' && !opponent.tier) ||
    (opponent.tier === 'Champion' && !fighter.tier)
  ) {
    risk += 0.2
  }

  // Convert risk to score (inverted)
  return Math.min(Math.max(1 - risk, 0), 1)
}

function generateWhy(
  fighter: FighterWithMetrics,
  opponent: FighterWithMetrics,
  components: MatchupScoreComponents
): string[] {
  const reasons: string[] = []

  if (components.competitiveness > 0.7) {
    if (fighter.rank !== null && opponent.rank !== null) {
      const rankDiff = Math.abs(fighter.rank - opponent.rank)
      if (rankDiff <= 2) {
        reasons.push(`Close rankings (#${fighter.rank} vs #${opponent.rank}) create a competitive matchup`)
      }
    }
    if (fighter.tier === opponent.tier && fighter.tier) {
      reasons.push(`Both fighters are ${fighter.tier.toLowerCase()}s, indicating similar skill level`)
    }
  }

  if (components.activity > 0.7) {
    const fighterDays = fighter.metrics?.days_since_fight ?? 365
    const opponentDays = opponent.metrics?.days_since_fight ?? 365
    if (fighterDays < 180 && opponentDays < 180) {
      reasons.push('Both fighters are recently active, ensuring readiness')
    }
  }

  if (components.excitement > 0.7) {
    const fighterFinishRate = fighter.metrics?.finish_rate ?? 0
    const opponentFinishRate = opponent.metrics?.finish_rate ?? 0
    if (fighterFinishRate > 0.7 || opponentFinishRate > 0.7) {
      reasons.push('High finish rates suggest an exciting, action-packed fight')
    }
  }

  if (components.risk < 0.3) {
    reasons.push('Low risk of mismatch, protecting both fighters')
  }

  if (reasons.length === 0) {
    reasons.push('Balanced matchup across multiple factors')
  }

  return reasons
}

function generateRisks(
  fighter: FighterWithMetrics,
  opponent: FighterWithMetrics,
  components: MatchupScoreComponents
): string[] {
  const risks: string[] = []

  if (components.competitiveness < 0.4) {
    if (fighter.rank !== null && opponent.rank !== null) {
      const rankDiff = Math.abs(fighter.rank - opponent.rank)
      if (rankDiff > 5) {
        risks.push(`Large ranking gap (#${fighter.rank} vs #${opponent.rank}) may indicate mismatch`)
      }
    }
  }

  if (components.activity < 0.4) {
    const fighterDays = fighter.metrics?.days_since_fight ?? 365
    const opponentDays = opponent.metrics?.days_since_fight ?? 365
    if (fighterDays > 365 || opponentDays > 365) {
      risks.push('One or both fighters have been inactive for over a year')
    }
  }

  if (components.risk < 0.3) {
    risks.push('Potential mismatch could lead to one-sided outcome')
  }

  if (fighter.tier === 'Champion' && (!opponent.tier || opponent.tier !== 'Contender')) {
    risks.push('Champion vs non-contender may not be competitive')
  }

  if (risks.length === 0) {
    risks.push('No significant risks identified')
  }

  return risks
}

