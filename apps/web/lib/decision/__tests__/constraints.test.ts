import { describe, it, expect } from 'vitest'
import { checkConstraints, hasBlockingViolations } from '../constraints'
import { getPolicy } from '../policy'
import type { Fighter } from '../types'

const createFighter = (
  id: string,
  rank: number,
  lastFightDate: Date | null = null,
  isChampion: boolean = false,
  isInjured: boolean = false
): Fighter => ({
  id,
  name: `Fighter ${id}`,
  rank,
  lastFightDate,
  popularityScore: 50,
  isChampion,
  isInjured,
})

describe('constraints', () => {
  describe('checkConstraints', () => {
    it('should block same fighter', () => {
      const fighter = createFighter('fighter-1', 1)
      const policy = getPolicy('Balanced')

      const violations = checkConstraints(fighter, fighter, policy)

      expect(violations.length).toBeGreaterThan(0)
      expect(violations[0].type).toBe('same_fighter')
      expect(violations[0].severity).toBe('blocking')
    })

    it('should block recent matchups when policy disallows', () => {
      const fighter1 = createFighter('fighter-1', 1)
      const fighter2 = createFighter('fighter-2', 2)
      const policy = getPolicy('Sporting Merit') // Doesn't allow recent matchups
      const recentMatchups = ['fighter-1-fighter-2']

      const violations = checkConstraints(fighter1, fighter2, policy, recentMatchups)

      expect(violations.some((v) => v.type === 'recent_matchup')).toBe(true)
    })

    it('should allow recent matchups when policy allows', () => {
      const fighter1 = createFighter('fighter-1', 1)
      const fighter2 = createFighter('fighter-2', 2)
      const policy = getPolicy('Business First') // Allows recent matchups
      const recentMatchups = ['fighter-1-fighter-2']

      const violations = checkConstraints(fighter1, fighter2, policy, recentMatchups)

      expect(violations.some((v) => v.type === 'recent_matchup')).toBe(false)
    })

    it('should block rank gap when exceeds max', () => {
      const fighter1 = createFighter('fighter-1', 1)
      const fighter10 = createFighter('fighter-10', 10)
      const policy = getPolicy('Sporting Merit') // maxRankGap: 5

      const violations = checkConstraints(fighter1, fighter10, policy)

      expect(violations.some((v) => v.type === 'rank_gap_too_high')).toBe(true)
    })

    it('should allow rank gap within limit', () => {
      const fighter1 = createFighter('fighter-1', 1)
      const fighter5 = createFighter('fighter-5', 5)
      const policy = getPolicy('Sporting Merit') // maxRankGap: 5

      const violations = checkConstraints(fighter1, fighter5, policy)

      expect(violations.some((v) => v.type === 'rank_gap_too_high')).toBe(false)
    })

    it('should block injured fighters when policy blocks', () => {
      const fighter1 = createFighter('fighter-1', 1, null, false, true)
      const fighter2 = createFighter('fighter-2', 2)
      const policy = getPolicy('Balanced') // blockInjured: true

      const violations = checkConstraints(fighter1, fighter2, policy)

      expect(violations.some((v) => v.type === 'injured_fighter')).toBe(true)
    })

    it('should enforce title fight eligibility', () => {
      const champion = createFighter('fighter-1', 1, null, 50, true, false)
      const fighter10 = createFighter('fighter-10', 10)
      const policy = getPolicy('Sporting Merit') // requireTitleEligibility: true

      const violations = checkConstraints(champion, fighter10, policy)

      expect(violations.some((v) => v.type === 'title_fight_eligibility')).toBe(true)
    })

    it('should warn about long inactivity', () => {
      const oldDate = new Date()
      oldDate.setDate(oldDate.getDate() - 500) // 500 days ago

      const fighter1 = createFighter('fighter-1', 1, oldDate)
      const fighter2 = createFighter('fighter-2', 2)
      const policy = getPolicy('Balanced') // maxDaysInactive: 450

      const violations = checkConstraints(fighter1, fighter2, policy)

      expect(violations.some((v) => v.type === 'inactive_too_long')).toBe(true)
    })
  })

  describe('hasBlockingViolations', () => {
    it('should return true if blocking violations exist', () => {
      const violations = [
        { type: 'same_fighter' as const, reason: 'test', severity: 'blocking' as const },
        { type: 'rank_gap_too_high' as const, reason: 'test', severity: 'warning' as const },
      ]

      expect(hasBlockingViolations(violations)).toBe(true)
    })

    it('should return false if only warnings exist', () => {
      const violations = [
        { type: 'inactive_too_long' as const, reason: 'test', severity: 'warning' as const },
      ]

      expect(hasBlockingViolations(violations)).toBe(false)
    })

    it('should return false if no violations', () => {
      expect(hasBlockingViolations([])).toBe(false)
    })
  })
})

