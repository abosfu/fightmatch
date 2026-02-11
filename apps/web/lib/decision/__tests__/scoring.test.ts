import { describe, it, expect } from 'vitest'
import { scoreMatchup, calculateTotalScore } from '../scoring'
import { getPolicy } from '../policy'
import type { Fighter, DivisionContext } from '../types'

const createFighter = (
  id: string,
  rank: number,
  lastFightDate: Date | null = null,
  popularityScore: number = 50,
  isChampion: boolean = false,
  isInjured: boolean = false
): Fighter => ({
  id,
  name: `Fighter ${id}`,
  rank,
  lastFightDate,
  popularityScore,
  isChampion,
  isInjured,
})

const MOCK_CONTEXT: DivisionContext = {
  weightClassId: 'test',
  weightClassName: 'Test Division',
  totalFighters: 15,
  championId: 'fighter-1',
}

describe('scoring', () => {
  describe('scoreMatchup', () => {
    it('should score adjacent ranks highly for fairness', () => {
      const fighter1 = createFighter('fighter-1', 1, new Date('2023-10-01'))
      const fighter2 = createFighter('fighter-2', 2, new Date('2023-10-01'))
      const policy = getPolicy('Sporting Merit')

      const breakdown = scoreMatchup(fighter1, fighter2, MOCK_CONTEXT, policy)

      expect(breakdown.fairness).toBeGreaterThan(0.9)
    })

    it('should penalize large rank gaps for fairness', () => {
      const fighter1 = createFighter('fighter-1', 1, new Date('2023-10-01'))
      const fighter10 = createFighter('fighter-10', 10, new Date('2023-10-01'))
      const policy = getPolicy('Sporting Merit')

      const breakdown = scoreMatchup(fighter1, fighter10, MOCK_CONTEXT, policy)

      expect(breakdown.fairness).toBeLessThan(0.5)
    })

    it('should reward active fighters for activity', () => {
      const recentDate = new Date()
      recentDate.setDate(recentDate.getDate() - 60) // 60 days ago

      const fighter1 = createFighter('fighter-1', 1, recentDate)
      const fighter2 = createFighter('fighter-2', 2, recentDate)
      const policy = getPolicy('Balanced')

      const breakdown = scoreMatchup(fighter1, fighter2, MOCK_CONTEXT, policy)

      expect(breakdown.activity).toBeGreaterThan(0.6)
    })

    it('should penalize long layoffs for activity', () => {
      const oldDate = new Date()
      oldDate.setDate(oldDate.getDate() - 400) // 400 days ago

      const fighter1 = createFighter('fighter-1', 1, oldDate)
      const fighter2 = createFighter('fighter-2', 2, oldDate)
      const policy = getPolicy('Balanced')

      const breakdown = scoreMatchup(fighter1, fighter2, MOCK_CONTEXT, policy)

      expect(breakdown.activity).toBeLessThan(0.4)
    })

    it('should reward high popularity for hype', () => {
      const fighter1 = createFighter('fighter-1', 1, new Date('2023-10-01'), 90)
      const fighter2 = createFighter('fighter-2', 2, new Date('2023-10-01'), 85)
      const policy = getPolicy('Business First')

      const breakdown = scoreMatchup(fighter1, fighter2, MOCK_CONTEXT, policy)

      expect(breakdown.hype).toBeGreaterThan(0.8)
    })

    it('should penalize injured fighters for risk', () => {
      const fighter1 = createFighter('fighter-1', 1, new Date('2023-10-01'), 50, false, true)
      const fighter2 = createFighter('fighter-2', 2, new Date('2023-10-01'))
      const policy = getPolicy('Balanced')

      const breakdown = scoreMatchup(fighter1, fighter2, MOCK_CONTEXT, policy)

      expect(breakdown.risk).toBeLessThan(0.8)
    })
  })

  describe('calculateTotalScore', () => {
    it('should calculate weighted total score', () => {
      const breakdown = {
        fairness: 0.8,
        divisionHealth: 0.7,
        risk: 0.9,
        hype: 0.6,
        activity: 0.8,
      }
      const policy = getPolicy('Balanced')

      const total = calculateTotalScore(breakdown, policy)

      expect(total).toBeGreaterThan(0)
      expect(total).toBeLessThanOrEqual(1)
    })

    it('should respect policy weights', () => {
      const breakdown = {
        fairness: 0.5,
        divisionHealth: 0.5,
        risk: 0.5,
        hype: 0.9, // High hype
        activity: 0.5,
      }

      const sportingPolicy = getPolicy('Sporting Merit')
      const businessPolicy = getPolicy('Business First')

      const sportingScore = calculateTotalScore(breakdown, sportingPolicy)
      const businessScore = calculateTotalScore(breakdown, businessPolicy)

      // Business First should score higher due to high hype weight
      expect(businessScore).toBeGreaterThan(sportingScore)
    })
  })
})

