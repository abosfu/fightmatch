import { describe, it, expect } from 'vitest'
import { scoreMatchup } from './matchup'
import type { Fighter, FighterMetrics } from '@fightmatch/shared'

const createFighter = (
  name: string,
  rank: number | null,
  tier: string | null,
  metrics: Partial<FighterMetrics> | null
): any => ({
  id: `fighter-${name}`,
  slug: name.toLowerCase().replace(/\s+/g, '-'),
  name,
  rank,
  tier,
  metrics: metrics
    ? {
        id: `metrics-${name}`,
        fighter_id: `fighter-${name}`,
        weight_class_id: 'wc-1',
        last_fight_date: '2023-10-01',
        days_since_fight: 120,
        win_streak: 3,
        loss_streak: 0,
        finish_rate: 0.75,
        total_fights: 20,
        wins: 15,
        losses: 5,
        draws: 0,
        no_contests: 0,
        avg_opponent_strength: 0.7,
        ...metrics,
      }
    : null,
})

describe('scoreMatchup', () => {
  it('should score a competitive matchup highly', () => {
    const fighter = createFighter('Fighter A', 1, 'Champion', { win_streak: 3 })
    const opponent = createFighter('Fighter B', 2, 'Contender', { win_streak: 2 })

    const result = scoreMatchup(fighter, opponent, {
      weightClassId: 'wc-1',
      allFightersInClass: 15,
    })

    expect(result.total).toBeGreaterThan(0.6)
    expect(result.components.competitiveness).toBeGreaterThan(0.6)
    expect(result.explanation.why.length).toBeGreaterThan(0)
  })

  it('should penalize large ranking gaps', () => {
    const fighter = createFighter('Top Fighter', 1, 'Champion', null)
    const opponent = createFighter('Low Ranked', 15, 'Prospect', null)

    const result = scoreMatchup(fighter, opponent, {
      weightClassId: 'wc-1',
      allFightersInClass: 15,
    })

    expect(result.components.competitiveness).toBeLessThan(0.5)
    expect(result.components.risk).toBeLessThan(0.5)
    expect(result.explanation.risks.some((r) => r.includes('ranking gap'))).toBe(true)
  })

  it('should reward high finish rates for excitement', () => {
    const fighter = createFighter('Finisher A', 3, 'Contender', { finish_rate: 0.9 })
    const opponent = createFighter('Finisher B', 4, 'Contender', { finish_rate: 0.85 })

    const result = scoreMatchup(fighter, opponent, {
      weightClassId: 'wc-1',
      allFightersInClass: 15,
    })

    expect(result.components.excitement).toBeGreaterThan(0.7)
    expect(result.explanation.why.some((w) => w.includes('finish'))).toBe(true)
  })

  it('should penalize inactive fighters', () => {
    const fighter = createFighter('Active Fighter', 5, 'Contender', {
      days_since_fight: 60,
    })
    const opponent = createFighter('Inactive Fighter', 6, 'Contender', {
      days_since_fight: 500,
    })

    const result = scoreMatchup(fighter, opponent, {
      weightClassId: 'wc-1',
      allFightersInClass: 15,
    })

    expect(result.components.activity).toBeLessThan(0.6)
    expect(result.explanation.risks.some((r) => r.includes('inactive'))).toBe(true)
  })

  it('should handle fighters without metrics gracefully', () => {
    const fighter = createFighter('Fighter A', 1, 'Champion', null)
    const opponent = createFighter('Fighter B', 2, 'Contender', null)

    const result = scoreMatchup(fighter, opponent, {
      weightClassId: 'wc-1',
      allFightersInClass: 15,
    })

    expect(result.total).toBeGreaterThanOrEqual(0)
    expect(result.total).toBeLessThanOrEqual(1)
    expect(result.components).toHaveProperty('competitiveness')
    expect(result.components).toHaveProperty('activity')
    expect(result.components).toHaveProperty('excitement')
    expect(result.components).toHaveProperty('risk')
  })
})

