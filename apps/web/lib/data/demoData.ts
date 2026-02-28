import type {
  WeightClass,
  Fighter,
  FighterWithWeightClass,
  FighterMetrics,
  FightWithParticipants,
  RankingEntryWithFighter,
} from '@fightmatch/shared'

const DEMO_WC_ID = 'wc-demo-lightweight'
const DEMO_WC_SLUG = 'lightweight'

const demoWeightClasses: WeightClass[] = [
  {
    id: DEMO_WC_ID,
    slug: DEMO_WC_SLUG,
    name: 'Lightweight',
    weight_limit_lbs: 155,
    created_at: undefined,
    updated_at: undefined,
  },
  {
    id: 'wc-demo-welterweight',
    slug: 'welterweight',
    name: 'Welterweight',
    weight_limit_lbs: 170,
    created_at: undefined,
    updated_at: undefined,
  },
]

const demoFighters: Fighter[] = [
  { id: 'fighter-1', slug: 'fighter-1', name: 'Demo Champion', ufcstats_id: null, date_of_birth: null, height_inches: null, reach_inches: null, stance: null },
  { id: 'fighter-2', slug: 'fighter-2', name: 'Demo Contender A', ufcstats_id: null, date_of_birth: null, height_inches: null, reach_inches: null, stance: null },
  { id: 'fighter-3', slug: 'fighter-3', name: 'Demo Contender B', ufcstats_id: null, date_of_birth: null, height_inches: null, reach_inches: null, stance: null },
  { id: 'fighter-4', slug: 'fighter-4', name: 'Demo Prospect', ufcstats_id: null, date_of_birth: null, height_inches: null, reach_inches: null, stance: null },
  { id: 'fighter-5', slug: 'fighter-5', name: 'Demo Up-and-Comer', ufcstats_id: null, date_of_birth: null, height_inches: null, reach_inches: null, stance: null },
]

function toFighterWithWeightClass(f: Fighter): FighterWithWeightClass {
  return {
    ...f,
    weight_class_id: DEMO_WC_ID,
    weight_class_slug: DEMO_WC_SLUG,
    weight_class_name: 'Lightweight',
  }
}

const demoMetrics: Record<string, FighterMetrics> = {
  'fighter-1': {
    id: 'm1',
    fighter_id: 'fighter-1',
    weight_class_id: DEMO_WC_ID,
    last_fight_date: '2024-01-15',
    days_since_fight: 45,
    win_streak: 4,
    loss_streak: 0,
    finish_rate: 0.6,
    total_fights: 20,
    wins: 16,
    losses: 4,
    draws: 0,
    no_contests: 0,
    avg_opponent_strength: 0.75,
  },
  'fighter-2': {
    id: 'm2',
    fighter_id: 'fighter-2',
    weight_class_id: DEMO_WC_ID,
    last_fight_date: '2024-02-01',
    days_since_fight: 30,
    win_streak: 2,
    loss_streak: 0,
    finish_rate: 0.5,
    total_fights: 18,
    wins: 14,
    losses: 4,
    draws: 0,
    no_contests: 0,
    avg_opponent_strength: 0.7,
  },
  'fighter-3': {
    id: 'm3',
    fighter_id: 'fighter-3',
    weight_class_id: DEMO_WC_ID,
    last_fight_date: '2023-11-01',
    days_since_fight: 120,
    win_streak: 1,
    loss_streak: 0,
    finish_rate: 0.4,
    total_fights: 15,
    wins: 11,
    losses: 4,
    draws: 0,
    no_contests: 0,
    avg_opponent_strength: 0.65,
  },
  'fighter-4': {
    id: 'm4',
    fighter_id: 'fighter-4',
    weight_class_id: DEMO_WC_ID,
    last_fight_date: '2024-03-01',
    days_since_fight: 10,
    win_streak: 3,
    loss_streak: 0,
    finish_rate: 0.8,
    total_fights: 10,
    wins: 8,
    losses: 2,
    draws: 0,
    no_contests: 0,
    avg_opponent_strength: 0.5,
  },
  'fighter-5': {
    id: 'm5',
    fighter_id: 'fighter-5',
    weight_class_id: DEMO_WC_ID,
    last_fight_date: null,
    days_since_fight: 400,
    win_streak: 0,
    loss_streak: 0,
    finish_rate: 0.5,
    total_fights: 5,
    wins: 4,
    losses: 1,
    draws: 0,
    no_contests: 0,
    avg_opponent_strength: 0.4,
  },
}

export async function getWeightClasses(): Promise<WeightClass[]> {
  return [...demoWeightClasses]
}

export async function getWeightClassBySlug(slug: string): Promise<WeightClass | null> {
  return demoWeightClasses.find((wc) => wc.slug === slug) ?? null
}

export async function getFightersByWeightClass(
  weightClassId: string,
  search?: string
): Promise<FighterWithWeightClass[]> {
  const list = demoWeightClasses.some((wc) => wc.id === weightClassId)
    ? demoFighters.map(toFighterWithWeightClass)
    : []
  if (search) {
    const q = search.toLowerCase()
    return list.filter((f) => f.name.toLowerCase().includes(q))
  }
  return list
}

export async function getFighterBySlug(slug: string): Promise<Fighter | null> {
  return demoFighters.find((f) => f.slug === slug) ?? null
}

export async function getFighterById(id: string): Promise<Fighter | null> {
  return demoFighters.find((f) => f.id === id) ?? null
}

export async function getFighterPrimaryWeightClass(fighterId: string): Promise<WeightClass | null> {
  return demoFighters.some((f) => f.id === fighterId) ? demoWeightClasses[0]! : null
}

export async function getFighterMetrics(
  _fighterId: string,
  weightClassId: string
): Promise<FighterMetrics | null> {
  if (weightClassId !== DEMO_WC_ID) return null
  return demoMetrics[_fighterId] ?? null
}

export async function getFighterRecentFights(
  fighterId: string,
  limit: number = 5
): Promise<FightWithParticipants[]> {
  const fighter = demoFighters.find((f) => f.id === fighterId)
  if (!fighter) return []
  const opponent = demoFighters.find((f) => f.id !== fighterId)
  if (!opponent) return []
  return [
    {
      id: 'fight-demo-1',
      event_id: null,
      date: '2024-01-15',
      weight_class_id: DEMO_WC_ID,
      result_type: 'KO/TKO',
      result_method: 'Punch',
      result_round: 3,
      result_time: '2:30',
      ufcstats_id: null,
      participants: [
        { id: 'fp1', fight_id: 'fight-demo-1', fighter_id: fighter.id, is_winner: true, is_champion: false, weight_lbs: null, fighter },
        { id: 'fp2', fight_id: 'fight-demo-1', fighter_id: opponent.id, is_winner: false, is_champion: false, weight_lbs: null, fighter: opponent },
      ],
    },
  ].slice(0, limit)
}

type CandidateWithMeta = FighterWithWeightClass & {
  metrics: FighterMetrics | null
  rank: number | null
  tier: string | null
}

export async function getCandidateOpponents(
  fighterId: string,
  weightClassId: string
): Promise<CandidateWithMeta[]> {
  if (weightClassId !== DEMO_WC_ID) return []
  const list = demoFighters
    .filter((f) => f.id !== fighterId)
    .map((f) => toFighterWithWeightClass(f))
  const rankTiers: Record<number, string> = {
    1: 'Champion',
    2: 'Contender',
    3: 'Contender',
    4: 'Prospect',
    5: 'Prospect',
  }
  return list.map((fighter, i) => ({
    ...fighter,
    metrics: demoMetrics[fighter.id] ?? null,
    rank: i + 2,
    tier: rankTiers[i + 2] ?? null,
  }))
}

export async function getRankingEntriesWithFighters(
  weightClassId: string
): Promise<RankingEntryWithFighter[]> {
  if (weightClassId !== DEMO_WC_ID) return []
  return demoFighters.map((fighter, i) => ({
    id: `re-${fighter.id}`,
    ranking_id: 'rank-demo-1',
    fighter_id: fighter.id,
    rank: i + 1,
    tier: i === 0 ? 'Champion' : i <= 2 ? 'Contender' : 'Prospect',
    fighter,
    metrics: demoMetrics[fighter.id] ?? null,
  }))
}
