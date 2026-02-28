import { getFighterById, getCandidateOpponents, getFighterPrimaryWeightClass, getWeightClassBySlug } from '@/lib/data/dataAccess'
import { scoreMatchup } from '@/lib/scoring/matchup'
import type { RecommendationResult } from '@fightmatch/shared'

export interface BlockedOpponent {
  opponentId: string
  opponentName: string
  reason: string
}

export interface DecisionResult {
  fighterId: string
  fighterName: string
  weightClassId: string
  weightClassName: string
  ranked: RecommendationResult[]
  blocked: BlockedOpponent[]
  assumptions: string[]
}

const INACTIVITY_DAYS_THRESHOLD = 400

export async function runDecision(
  fighterId: string,
  weightClassIdOrSlug?: string
): Promise<DecisionResult | null> {
  const fighter = await getFighterById(fighterId)
  if (!fighter) return null

  let weightClassId = weightClassIdOrSlug
  if (!weightClassId) {
    const primary = await getFighterPrimaryWeightClass(fighterId)
    if (!primary) return null
    weightClassId = primary.id
  } else if (!weightClassId.startsWith('wc-') && !weightClassId.includes('-')) {
    const wc = await getWeightClassBySlug(weightClassId)
    if (!wc) return null
    weightClassId = wc.id
  }

  const allCandidates = await getCandidateOpponents(fighterId, weightClassId)
  const weightClassName = allCandidates[0]?.weight_class_name ?? 'Unknown'

  const blocked: BlockedOpponent[] = []
  const candidates: typeof allCandidates = []

  for (const c of allCandidates) {
    const daysInactive = c.metrics?.days_since_fight ?? 999
    if (daysInactive > INACTIVITY_DAYS_THRESHOLD) {
      blocked.push({
        opponentId: c.id,
        opponentName: c.name,
        reason: `Inactive ${daysInactive} days (over ${INACTIVITY_DAYS_THRESHOLD}-day policy limit)`,
      })
      continue
    }
    candidates.push(c)
  }

  const selfData = allCandidates.find((c) => c.id === fighterId) ?? {
    ...fighter,
    metrics: null,
    rank: null,
    tier: null,
    weight_class_id: weightClassId,
    weight_class_slug: 'lightweight',
    weight_class_name: weightClassName,
  }

  const ranked: RecommendationResult[] = candidates
    .map((opponent) => {
      const score = scoreMatchup(selfData as any, opponent as any, {
        weightClassId,
        allFightersInClass: allCandidates.length + 1,
      })
      return {
        opponent: {
          ...opponent,
          metrics: opponent.metrics,
          rank: opponent.rank,
          tier: opponent.tier,
        },
        score,
      }
    })
    .sort((a, b) => b.score.total - a.score.total)
    .slice(0, 10)

  const assumptions = [
    'Rank proximity, activity, excitement, and risk are weighted equally.',
    'Blocked: opponents inactive over ' + INACTIVITY_DAYS_THRESHOLD + ' days.',
    'Recommendations are for the same weight class only.',
  ]

  return {
    fighterId: fighter.id,
    fighterName: fighter.name,
    weightClassId,
    weightClassName,
    ranked,
    blocked,
    assumptions,
  }
}
