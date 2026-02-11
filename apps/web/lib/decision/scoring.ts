/**
 * Multi-objective scoring for matchup recommendations
 * All scores normalized to 0-1 range
 */

import type { Fighter, MatchupScoreBreakdown, Policy, DivisionContext } from './types'

/**
 * Calculate all metric scores for a matchup
 */
export function scoreMatchup(
  targetFighter: Fighter,
  candidateFighter: Fighter,
  context: DivisionContext,
  policy: Policy
): MatchupScoreBreakdown {
  return {
    fairness: scoreFairness(targetFighter, candidateFighter, context),
    divisionHealth: scoreDivisionHealth(targetFighter, candidateFighter, context),
    risk: scoreRisk(targetFighter, candidateFighter),
    hype: scoreHype(targetFighter, candidateFighter),
    activity: scoreActivity(targetFighter, candidateFighter),
  }
}

/**
 * Calculate weighted total score
 */
export function calculateTotalScore(
  breakdown: MatchupScoreBreakdown,
  policy: Policy
): number {
  const { weights } = policy
  const weightedSum =
    breakdown.fairness * weights.fairness +
    breakdown.divisionHealth * weights.divisionHealth +
    breakdown.risk * weights.risk +
    breakdown.hype * weights.hype +
    breakdown.activity * weights.activity

  const totalWeight =
    weights.fairness +
    weights.divisionHealth +
    weights.risk +
    weights.hype +
    weights.activity

  return totalWeight > 0 ? weightedSum / totalWeight : 0
}

/**
 * Fairness: Penalize large rank gaps, reward adjacent ranks
 * Score: 1.0 for adjacent ranks, decreases as gap increases
 */
function scoreFairness(
  targetFighter: Fighter,
  candidateFighter: Fighter,
  context: DivisionContext
): number {
  const rankGap = Math.abs(targetFighter.rank - candidateFighter.rank)
  const maxGap = context.totalFighters - 1

  if (maxGap === 0) return 1.0

  // Adjacent ranks (gap = 1) = 1.0
  // Max gap = 0.1 (still some value, but very low)
  if (rankGap === 0) return 0.0 // Same rank (shouldn't happen, but handle it)
  if (rankGap === 1) return 1.0

  // Exponential decay: 1.0 * (0.1^(gap/maxGap))
  const decayFactor = Math.pow(0.1, rankGap / maxGap)
  return Math.max(0.1, decayFactor)
}

/**
 * Division Health: Reward fights that reduce "logjams"
 * Logjam = multiple fighters with similar ranks who haven't fought
 * Score based on how much this matchup would clarify the division
 */
function scoreDivisionHealth(
  targetFighter: Fighter,
  candidateFighter: Fighter,
  context: DivisionContext
): number {
  const rankGap = Math.abs(targetFighter.rank - candidateFighter.rank)

  // Fights between adjacent ranks (1-2, 2-3) are most valuable
  if (rankGap <= 2) {
    return 1.0
  }

  // Fights between ranks 3-5 apart are moderately valuable
  if (rankGap <= 5) {
    return 0.7
  }

  // Fights between ranks 6-10 apart are less valuable
  if (rankGap <= 10) {
    return 0.4
  }

  // Very large gaps don't help division health much
  return 0.2
}

/**
 * Risk: Penalize uncertainty (inverted - higher score = lower risk)
 * Factors: long layoffs, injury status, inactivity
 */
function scoreRisk(targetFighter: Fighter, candidateFighter: Fighter): number {
  let risk = 0.5 // Base risk

  // Check layoffs
  const targetDaysInactive = getDaysInactive(targetFighter)
  const candidateDaysInactive = getDaysInactive(candidateFighter)

  // High risk if either fighter inactive > 12 months
  if (targetDaysInactive > 365 || candidateDaysInactive > 365) {
    risk += 0.3
  } else if (targetDaysInactive > 180 || candidateDaysInactive > 180) {
    risk += 0.15
  }

  // Injury status
  if (targetFighter.isInjured || candidateFighter.isInjured) {
    risk += 0.2
  }

  // Invert: higher risk = lower score
  return Math.max(0, 1 - Math.min(1, risk))
}

/**
 * Hype/Revenue: Proxy with popularity scores
 * Higher combined popularity = more hype
 */
function scoreHype(targetFighter: Fighter, candidateFighter: Fighter): number {
  const avgPopularity = (targetFighter.popularityScore + candidateFighter.popularityScore) / 2
  // Normalize 0-100 to 0-1
  return avgPopularity / 100
}

/**
 * Activity: Reward fighters active within last X months, penalize long layoffs
 * Ideal: both fighters active within last 6 months
 */
function scoreActivity(targetFighter: Fighter, candidateFighter: Fighter): number {
  const targetDays = getDaysInactive(targetFighter)
  const candidateDays = getDaysInactive(candidateFighter)

  // Ideal: both active within 6 months (180 days)
  const idealDays = 180
  const targetScore = Math.max(0, 1 - targetDays / (idealDays * 2))
  const candidateScore = Math.max(0, 1 - candidateDays / (idealDays * 2))

  // Average, but also reward compatibility (both similarly active)
  const avgScore = (targetScore + candidateScore) / 2
  const compatibility = 1 - Math.abs(targetScore - candidateScore) * 0.5

  return (avgScore * 0.7 + compatibility * 0.3)
}

/**
 * Helper: Get days since last fight
 */
function getDaysInactive(fighter: Fighter): number {
  if (!fighter.lastFightDate) {
    return 9999
  }
  const now = new Date()
  const diffTime = now.getTime() - fighter.lastFightDate.getTime()
  return Math.floor(diffTime / (1000 * 60 * 60 * 24))
}

