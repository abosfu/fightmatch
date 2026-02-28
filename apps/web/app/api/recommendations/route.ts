import { NextResponse } from 'next/server'
import { getFighterById, getCandidateOpponents, getWeightClassBySlug, getFighterPrimaryWeightClass } from '@/lib/data/dataAccess'
import { scoreMatchup } from '@/lib/scoring/matchup'
import type { RecommendationResult } from '@fightmatch/shared'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const fighterId = searchParams.get('fighterId')
    const weightClassId = searchParams.get('weightClassId')
    const weightClassSlug = searchParams.get('weightClassSlug')

    if (!fighterId) {
      return NextResponse.json({ error: 'fighterId is required' }, { status: 400 })
    }

    const fighter = await getFighterById(fighterId)
    if (!fighter) {
      return NextResponse.json({ error: 'Fighter not found' }, { status: 404 })
    }

    let wcId = weightClassId
    if (!wcId && weightClassSlug) {
      const wc = await getWeightClassBySlug(weightClassSlug)
      if (!wc) {
        return NextResponse.json({ error: 'Weight class not found' }, { status: 404 })
      }
      wcId = wc.id
    }

    // If no weight class provided, get fighter's primary weight class
    if (!wcId) {
      const primaryWc = await getFighterPrimaryWeightClass(fighterId)
      if (!primaryWc) {
        return NextResponse.json({ error: 'Fighter has no primary weight class' }, { status: 400 })
      }
      wcId = primaryWc.id
    }

    const candidates = await getCandidateOpponents(fighterId, wcId)

    // Get fighter's own data for scoring
    const fighterWithData = candidates.find((c) => c.id === fighterId) || {
      ...fighter,
      metrics: null,
      rank: null,
      tier: null,
    }

    // Score all matchups
    const scored: RecommendationResult[] = candidates
      .filter((c) => c.id !== fighterId)
      .map((opponent) => {
        const score = scoreMatchup(fighterWithData as any, opponent as any, {
          weightClassId: wcId!,
          allFightersInClass: candidates.length,
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
      .slice(0, 5)

    return NextResponse.json(scored)
  } catch (error) {
    console.error('Error generating recommendations:', error)
    return NextResponse.json({ error: 'Failed to generate recommendations' }, { status: 500 })
  }
}

