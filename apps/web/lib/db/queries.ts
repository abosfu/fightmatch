import { supabaseServer } from './supabaseServer'
import type {
  WeightClass,
  Fighter,
  FighterWithWeightClass,
  FighterMetrics,
  Fight,
  FightWithParticipants,
  RankingEntryWithFighter,
} from '@fightmatch/shared'

function guardSupabase() {
  if (!supabaseServer) throw new Error('Supabase not configured')
}

export async function getWeightClasses(): Promise<WeightClass[]> {
  guardSupabase()
  const { data, error } = await supabaseServer!
    .from('weight_classes')
    .select('*')
    .order('weight_limit_lbs', { ascending: true })

  if (error) throw error
  return data || []
}

export async function getWeightClassBySlug(slug: string): Promise<WeightClass | null> {
  guardSupabase()
  const { data, error } = await supabaseServer!
    .from('weight_classes')
    .select('*')
    .eq('slug', slug)
    .single()

  if (error) {
    if (error.code === 'PGRST116') return null
    throw error
  }
  return data
}

export async function getFightersByWeightClass(
  weightClassId: string,
  search?: string
): Promise<FighterWithWeightClass[]> {
  guardSupabase()
  let query = supabaseServer!
    .from('fighter_weight_class')
    .select(`
      fighter_id,
      weight_class_id,
      fighters!inner(*),
      weight_classes!inner(slug, name)
    `)
    .eq('weight_class_id', weightClassId)

  if (search) {
    query = query.ilike('fighters.name', `%${search}%`)
  }

  const { data, error } = await query.order('fighters.name', { ascending: true })

  if (error) throw error

  return (data || []).map((row: any) => ({
    ...row.fighters,
    weight_class_id: row.weight_class_id,
    weight_class_slug: row.weight_classes.slug,
    weight_class_name: row.weight_classes.name,
  }))
}

export async function getFighterBySlug(slug: string): Promise<Fighter | null> {
  guardSupabase()
  const { data, error } = await supabaseServer!
    .from('fighters')
    .select('*')
    .eq('slug', slug)
    .single()

  if (error) {
    if (error.code === 'PGRST116') return null
    throw error
  }
  return data
}

export async function getFighterById(id: string): Promise<Fighter | null> {
  guardSupabase()
  const { data, error } = await supabaseServer!
    .from('fighters')
    .select('*')
    .eq('id', id)
    .single()

  if (error) {
    if (error.code === 'PGRST116') return null
    throw error
  }
  return data
}

export async function getFighterPrimaryWeightClass(fighterId: string): Promise<WeightClass | null> {
  guardSupabase()
  const { data, error } = await supabaseServer!
    .from('fighter_weight_class')
    .select('weight_classes(*)')
    .eq('fighter_id', fighterId)
    .eq('is_primary', true)
    .single()

  if (error) {
    if (error.code === 'PGRST116') return null
    throw error
  }
  return (data as any)?.weight_classes || null
}

export async function getFighterMetrics(
  fighterId: string,
  weightClassId: string
): Promise<FighterMetrics | null> {
  guardSupabase()
  const { data, error } = await supabaseServer!
    .from('fighter_metrics')
    .select('*')
    .eq('fighter_id', fighterId)
    .eq('weight_class_id', weightClassId)
    .single()

  if (error) {
    if (error.code === 'PGRST116') return null
    throw error
  }
  return data
}

export async function getFighterRecentFights(
  fighterId: string,
  limit: number = 5
): Promise<FightWithParticipants[]> {
  guardSupabase()
  const { data: participants, error } = await supabaseServer!
    .from('fight_participants')
    .select(`
      fight_id,
      is_winner,
      is_champion,
      fights!inner(
        *,
        participants:fight_participants(
          *,
          fighters(*)
        )
      )
    `)
    .eq('fighter_id', fighterId)
    .order('fights.date', { ascending: false })
    .limit(limit)

  if (error) throw error

  return (participants || []).map((p: any) => ({
    ...p.fights,
    participants: p.fights.participants.map((fp: any) => ({
      ...fp,
      fighter: fp.fighters,
    })),
  }))
}

export async function getCandidateOpponents(
  fighterId: string,
  weightClassId: string
): Promise<(FighterWithWeightClass & { metrics: FighterMetrics | null; rank: number | null; tier: string | null })[]> {
  try {
    // Get the fighter's primary weight class
    const fighter = await getFighterById(fighterId)
    if (!fighter) return []

    // Get all fighters in the same weight class (excluding self)
    const fighters = await getFightersByWeightClass(weightClassId)
    const candidates = fighters.filter((f) => f.id !== fighterId)

    // Get latest ranking for this weight class
    const { data: ranking, error: rankingError } = await supabaseServer!
      .from('rankings')
      .select('id')
      .eq('weight_class_id', weightClassId)
      .order('snapshot_date', { ascending: false })
      .limit(1)
      .single()

    // Get ranking entries (ignore errors if no ranking exists)
    const rankingEntries: Record<string, { rank: number; tier: string | null }> = {}
    if (ranking && !rankingError) {
      const { data: entries, error: entriesError } = await supabaseServer!
        .from('ranking_entries')
        .select('fighter_id, rank, tier')
        .eq('ranking_id', ranking.id)

      if (entries && !entriesError) {
        entries.forEach((entry) => {
          rankingEntries[entry.fighter_id] = { rank: entry.rank, tier: entry.tier }
        })
      }
    }

    // Get metrics for all candidates (ignore errors if no metrics exist)
    const candidateIds = candidates.map((f) => f.id)
    let metrics = null
    let metricsError = null
    if (candidateIds.length > 0) {
      const result = await supabaseServer!
        .from('fighter_metrics')
        .select('*')
        .eq('weight_class_id', weightClassId)
        .in('fighter_id', candidateIds)
      metrics = result.data
      metricsError = result.error
    }

    const metricsMap: Record<string, FighterMetrics> = {}
    if (metrics && !metricsError) {
      metrics.forEach((m) => {
        metricsMap[m.fighter_id] = m
      })
    }

    return candidates.map((fighter) => ({
      ...fighter,
      metrics: metricsMap[fighter.id] || null,
      rank: rankingEntries[fighter.id]?.rank || null,
      tier: rankingEntries[fighter.id]?.tier || null,
    }))
  } catch (error) {
    console.error('Error in getCandidateOpponents:', error)
    // Return empty array on error rather than throwing
    return []
  }
}

export async function getRankingEntriesWithFighters(
  weightClassId: string
): Promise<RankingEntryWithFighter[]> {
  // Get latest ranking
  guardSupabase()
  const { data: ranking } = await supabaseServer!
    .from('rankings')
    .select('id')
    .eq('weight_class_id', weightClassId)
    .order('snapshot_date', { ascending: false })
    .limit(1)
    .single()

  if (!ranking) return []

  const { data, error } = await supabaseServer!
    .from('ranking_entries')
    .select(`
      *,
      fighters(*)
    `)
    .eq('ranking_id', ranking.id)
    .order('rank', { ascending: true })

  if (error) throw error

  // Get metrics for all fighters
  const fighterIds = (data || []).map((entry: any) => entry.fighter_id)
  const { data: metrics } = await supabaseServer!
    .from('fighter_metrics')
    .select('*')
    .eq('weight_class_id', weightClassId)
    .in('fighter_id', fighterIds)

  const metricsMap: Record<string, FighterMetrics> = {}
  if (metrics) {
    metrics.forEach((m) => {
      metricsMap[m.fighter_id] = m
    })
  }

  return (data || []).map((entry: any) => ({
    ...entry,
    fighter: entry.fighters,
    metrics: metricsMap[entry.fighter_id] || null,
  }))
}

