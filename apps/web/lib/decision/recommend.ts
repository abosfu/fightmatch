/**
 * Recommendation engine
 * Given target fighter, candidates, context, and policy, return ranked recommendations
 */

import type {
  Fighter,
  MatchupCandidate,
  RecommendationResult,
  DivisionContext,
  Policy,
} from './types'
import { checkConstraints, hasBlockingViolations } from './constraints'
import { scoreMatchup, calculateTotalScore } from './scoring'

/**
 * Generate recommendations for a target fighter
 */
export function recommend(
  targetFighter: Fighter,
  candidateFighters: Fighter[],
  context: DivisionContext,
  policy: Policy,
  recentMatchups: string[] = [] // TODO: Get from Supabase fights table
): RecommendationResult {
  const candidates: MatchupCandidate[] = []
  const blocked: MatchupCandidate[] = []

  // Score each candidate
  for (const candidate of candidateFighters) {
    // Check constraints
    const violations = checkConstraints(
      targetFighter,
      candidate,
      policy,
      recentMatchups
    )

    // Calculate scores
    const breakdown = scoreMatchup(targetFighter, candidate, context, policy)
    const totalScore = calculateTotalScore(breakdown, policy)

    // Generate explanation
    const explanation = generateExplanation(
      targetFighter,
      candidate,
      breakdown,
      policy
    )

    const matchupCandidate: MatchupCandidate = {
      fighter: candidate,
      totalScore,
      breakdown,
      violations,
      explanation,
    }

    // Separate eligible from blocked
    if (hasBlockingViolations(violations)) {
      blocked.push(matchupCandidate)
    } else {
      candidates.push(matchupCandidate)
    }
  }

  // Sort by total score (descending)
  candidates.sort((a, b) => b.totalScore - a.totalScore)
  blocked.sort((a, b) => b.totalScore - a.totalScore)

  return {
    targetFighter,
    candidates,
    blocked,
    policy,
    context,
  }
}

/**
 * Generate human-readable explanation for a recommendation
 * Cites top 2-3 reasons for the ranking
 */
function generateExplanation(
  targetFighter: Fighter,
  candidateFighter: Fighter,
  breakdown: MatchupScoreBreakdown,
  policy: Policy
): string {
  const reasons: string[] = []

  // Top scoring metrics
  const metrics = [
    { name: 'fairness', score: breakdown.fairness, label: 'Competitive fairness' },
    { name: 'divisionHealth', score: breakdown.divisionHealth, label: 'Division clarity' },
    { name: 'risk', score: breakdown.risk, label: 'Low risk' },
    { name: 'hype', score: breakdown.hype, label: 'Fan interest' },
    { name: 'activity', score: breakdown.activity, label: 'Fighter readiness' },
  ]

  // Sort by score and take top 2-3
  metrics.sort((a, b) => b.score - a.score)
  const topMetrics = metrics.slice(0, 3).filter((m) => m.score > 0.5)

  for (const metric of topMetrics) {
    if (metric.score > 0.7) {
      reasons.push(`Strong ${metric.label.toLowerCase()} (${Math.round(metric.score * 100)}%)`)
    } else if (metric.score > 0.5) {
      reasons.push(`Good ${metric.label.toLowerCase()} (${Math.round(metric.score * 100)}%)`)
    }
  }

  // Add rank context
  const rankGap = Math.abs(targetFighter.rank - candidateFighter.rank)
  if (rankGap <= 2) {
    reasons.push('Close rankings create competitive matchup')
  }

  // Add champion context
  if (targetFighter.isChampion || candidateFighter.isChampion) {
    reasons.push('Title fight potential')
  }

  if (reasons.length === 0) {
    return 'Balanced matchup across multiple factors'
  }

  return reasons.slice(0, 3).join('. ') + '.'
}

