/**
 * Constraint checking for matchup eligibility
 * Returns violations with human-readable reasons
 */

import type { Fighter, ConstraintViolation, Policy } from './types'

/**
 * Check all constraints for a candidate matchup
 */
export function checkConstraints(
  targetFighter: Fighter,
  candidateFighter: Fighter,
  policy: Policy,
  recentMatchups: string[] = [] // Array of fighter ID pairs that fought recently
): ConstraintViolation[] {
  const violations: ConstraintViolation[] = []

  // Same fighter
  if (targetFighter.id === candidateFighter.id) {
    violations.push({
      type: 'same_fighter',
      reason: 'Cannot match a fighter against themselves',
      severity: 'blocking',
    })
  }

  // Recent matchup
  if (!policy.constraints.allowRecentMatchup) {
    const matchupKey1 = `${targetFighter.id}-${candidateFighter.id}`
    const matchupKey2 = `${candidateFighter.id}-${targetFighter.id}`
    if (recentMatchups.includes(matchupKey1) || recentMatchups.includes(matchupKey2)) {
      violations.push({
        type: 'recent_matchup',
        reason: 'These fighters have already fought recently',
        severity: 'blocking',
      })
    }
  }

  // Title fight eligibility
  if (policy.constraints.requireTitleEligibility) {
    if (targetFighter.isChampion && candidateFighter.rank > 5) {
      violations.push({
        type: 'title_fight_eligibility',
        reason: 'Champion can only fight top 5 contenders for title fights',
        severity: 'blocking',
      })
    }
    if (candidateFighter.isChampion && targetFighter.rank > 5) {
      violations.push({
        type: 'title_fight_eligibility',
        reason: 'Only top 5 contenders are eligible for title fights',
        severity: 'blocking',
      })
    }
  }

  // Rank gap
  if (policy.constraints.maxRankGap !== null) {
    const rankGap = Math.abs(targetFighter.rank - candidateFighter.rank)
    if (rankGap > policy.constraints.maxRankGap) {
      violations.push({
        type: 'rank_gap_too_high',
        reason: `Rank gap (${rankGap}) exceeds maximum allowed (${policy.constraints.maxRankGap})`,
        severity: 'blocking',
      })
    }
  }

  // Injured fighter
  if (policy.constraints.blockInjured) {
    if (targetFighter.isInjured) {
      violations.push({
        type: 'injured_fighter',
        reason: 'Target fighter is currently injured',
        severity: 'blocking',
      })
    }
    if (candidateFighter.isInjured) {
      violations.push({
        type: 'injured_fighter',
        reason: 'Candidate fighter is currently injured',
        severity: 'blocking',
      })
    }
  }

  // Inactive too long
  if (policy.constraints.maxDaysInactive !== null) {
    const daysInactive = getDaysInactive(targetFighter)
    if (daysInactive > policy.constraints.maxDaysInactive) {
      violations.push({
        type: 'inactive_too_long',
        reason: `Target fighter has been inactive for ${daysInactive} days (max: ${policy.constraints.maxDaysInactive})`,
        severity: 'warning',
      })
    }
    const candidateDaysInactive = getDaysInactive(candidateFighter)
    if (candidateDaysInactive > policy.constraints.maxDaysInactive) {
      violations.push({
        type: 'inactive_too_long',
        reason: `Candidate fighter has been inactive for ${candidateDaysInactive} days (max: ${policy.constraints.maxDaysInactive})`,
        severity: 'warning',
      })
    }
  }

  return violations
}

/**
 * Check if a candidate has any blocking violations
 */
export function hasBlockingViolations(violations: ConstraintViolation[]): boolean {
  return violations.some((v) => v.severity === 'blocking')
}

/**
 * Helper: Get days since last fight
 */
function getDaysInactive(fighter: Fighter): number {
  if (!fighter.lastFightDate) {
    return 9999 // Very high number if never fought
  }
  const now = new Date()
  const diffTime = now.getTime() - fighter.lastFightDate.getTime()
  return Math.floor(diffTime / (1000 * 60 * 60 * 24))
}

