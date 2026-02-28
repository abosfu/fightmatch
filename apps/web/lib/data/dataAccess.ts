import { dataMode } from './dataMode'
import * as demoData from './demoData'
import type {
  WeightClass,
  Fighter,
  FighterWithWeightClass,
  FighterMetrics,
  FightWithParticipants,
  RankingEntryWithFighter,
} from '@fightmatch/shared'

type CandidateWithMeta = FighterWithWeightClass & {
  metrics: FighterMetrics | null
  rank: number | null
  tier: string | null
}

export async function getWeightClasses(): Promise<WeightClass[]> {
  if (dataMode() === 'demo') return demoData.getWeightClasses()
  const q = await import('@/lib/db/queries')
  return q.getWeightClasses()
}

export async function getWeightClassBySlug(slug: string): Promise<WeightClass | null> {
  if (dataMode() === 'demo') return demoData.getWeightClassBySlug(slug)
  const q = await import('@/lib/db/queries')
  return q.getWeightClassBySlug(slug)
}

export async function getFightersByWeightClass(
  weightClassId: string,
  search?: string
): Promise<FighterWithWeightClass[]> {
  if (dataMode() === 'demo') return demoData.getFightersByWeightClass(weightClassId, search)
  const q = await import('@/lib/db/queries')
  return q.getFightersByWeightClass(weightClassId, search)
}

export async function getFighterBySlug(slug: string): Promise<Fighter | null> {
  if (dataMode() === 'demo') return demoData.getFighterBySlug(slug)
  const q = await import('@/lib/db/queries')
  return q.getFighterBySlug(slug)
}

export async function getFighterById(id: string): Promise<Fighter | null> {
  if (dataMode() === 'demo') return demoData.getFighterById(id)
  const q = await import('@/lib/db/queries')
  return q.getFighterById(id)
}

export async function getFighterPrimaryWeightClass(fighterId: string): Promise<WeightClass | null> {
  if (dataMode() === 'demo') return demoData.getFighterPrimaryWeightClass(fighterId)
  const q = await import('@/lib/db/queries')
  return q.getFighterPrimaryWeightClass(fighterId)
}

export async function getFighterMetrics(
  fighterId: string,
  weightClassId: string
): Promise<FighterMetrics | null> {
  if (dataMode() === 'demo') return demoData.getFighterMetrics(fighterId, weightClassId)
  const q = await import('@/lib/db/queries')
  return q.getFighterMetrics(fighterId, weightClassId)
}

export async function getFighterRecentFights(
  fighterId: string,
  limit: number = 5
): Promise<FightWithParticipants[]> {
  if (dataMode() === 'demo') return demoData.getFighterRecentFights(fighterId, limit)
  const q = await import('@/lib/db/queries')
  return q.getFighterRecentFights(fighterId, limit)
}

export async function getCandidateOpponents(
  fighterId: string,
  weightClassId: string
): Promise<CandidateWithMeta[]> {
  if (dataMode() === 'demo') return demoData.getCandidateOpponents(fighterId, weightClassId)
  const q = await import('@/lib/db/queries')
  return q.getCandidateOpponents(fighterId, weightClassId)
}

export async function getRankingEntriesWithFighters(
  weightClassId: string
): Promise<RankingEntryWithFighter[]> {
  if (dataMode() === 'demo') return demoData.getRankingEntriesWithFighters(weightClassId)
  const q = await import('@/lib/db/queries')
  return q.getRankingEntriesWithFighters(weightClassId)
}

export { dataMode }

export type HealthResult =
  | { ok: true; db: 'connected'; counts: { fighters: number; fights: number; events: number } }
  | { ok: true; db: 'demo'; counts?: { fighters: number; fights: number; events: number } }
  | { ok: false; db: 'error'; error: string; details?: string[] }

export async function getHealth(): Promise<HealthResult> {
  if (dataMode() === 'demo') {
    const wcs = await demoData.getWeightClasses()
    const fighters = await demoData.getFightersByWeightClass(wcs[0]?.id ?? '')
    return { ok: true, db: 'demo', counts: { fighters: fighters.length, fights: 1, events: 1 } }
  }
  const { supabaseServer } = await import('@/lib/db/supabaseServer')
  if (!supabaseServer) return { ok: false, db: 'error', error: 'Supabase not configured' }
  try {
    const [fightersResult, fightsResult, eventsResult] = await Promise.allSettled([
      supabaseServer.from('fighters').select('id', { count: 'exact', head: true }),
      supabaseServer.from('fights').select('id', { count: 'exact', head: true }),
      supabaseServer.from('events').select('id', { count: 'exact', head: true }),
    ])
    const fightersCount = fightersResult.status === 'fulfilled' ? fightersResult.value.count ?? 0 : 0
    const fightsCount = fightsResult.status === 'fulfilled' ? fightsResult.value.count ?? 0 : 0
    const eventsCount = eventsResult.status === 'fulfilled' ? eventsResult.value.count ?? 0 : 0
    const hasErrors = fightersResult.status === 'rejected' || fightsResult.status === 'rejected' || eventsResult.status === 'rejected'
    if (hasErrors) {
      const details = [fightersResult, fightsResult, eventsResult]
        .filter((r) => r.status === 'rejected')
        .map((r) => (r as PromiseRejectedResult).reason?.message ?? String((r as PromiseRejectedResult).reason))
      return { ok: false, db: 'error', error: 'Database connection failed', details }
    }
    return { ok: true, db: 'connected', counts: { fighters: fightersCount, fights: fightsCount, events: eventsCount } }
  } catch (error: any) {
    return { ok: false, db: 'error', error: error?.message ?? 'Unknown error' }
  }
}
