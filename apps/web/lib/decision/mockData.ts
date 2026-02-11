/**
 * Mock data for Decision Support Engine
 * TODO: Replace with Supabase queries
 * - Get fighters from fighters table
 * - Get rankings from ranking_entries table
 * - Get recent matchups from fights + fight_participants tables
 * - Get injury status from fighter_metrics or separate injuries table
 */

import type { Fighter, DivisionContext } from './types'

export const MOCK_DIVISION: DivisionContext = {
  weightClassId: 'lightweight',
  weightClassName: 'Lightweight',
  totalFighters: 12,
  championId: 'fighter-1',
}

export const MOCK_FIGHTERS: Fighter[] = [
  {
    id: 'fighter-1',
    name: 'Islam Makhachev',
    rank: 1,
    lastFightDate: new Date('2023-10-21'),
    popularityScore: 85,
    isChampion: true,
    isInjured: false,
  },
  {
    id: 'fighter-2',
    name: 'Charles Oliveira',
    rank: 2,
    lastFightDate: new Date('2023-06-10'),
    popularityScore: 80,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-3',
    name: 'Justin Gaethje',
    rank: 3,
    lastFightDate: new Date('2023-07-29'),
    popularityScore: 75,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-4',
    name: 'Dustin Poirier',
    rank: 4,
    lastFightDate: new Date('2023-07-29'),
    popularityScore: 82,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-5',
    name: 'Beneil Dariush',
    rank: 5,
    lastFightDate: new Date('2023-05-06'),
    popularityScore: 60,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-6',
    name: 'Arman Tsarukyan',
    rank: 6,
    lastFightDate: new Date('2023-12-02'),
    popularityScore: 65,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-7',
    name: 'Mateusz Gamrot',
    rank: 7,
    lastFightDate: new Date('2023-09-16'),
    popularityScore: 55,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-8',
    name: 'Rafael Fiziev',
    rank: 8,
    lastFightDate: new Date('2023-03-18'),
    popularityScore: 70,
    isChampion: false,
    isInjured: true, // Injured
  },
  {
    id: 'fighter-9',
    name: 'Dan Hooker',
    rank: 9,
    lastFightDate: new Date('2022-11-12'), // Long layoff
    popularityScore: 68,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-10',
    name: 'Jalin Turner',
    rank: 10,
    lastFightDate: new Date('2023-09-16'),
    popularityScore: 58,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-11',
    name: 'Bobby Green',
    rank: 11,
    lastFightDate: new Date('2023-12-16'),
    popularityScore: 50,
    isChampion: false,
    isInjured: false,
  },
  {
    id: 'fighter-12',
    name: 'Grant Dawson',
    rank: 12,
    lastFightDate: new Date('2023-10-07'),
    popularityScore: 45,
    isChampion: false,
    isInjured: false,
  },
]

// Recent matchups (fighter ID pairs)
// TODO: Get from Supabase fights table
export const MOCK_RECENT_MATCHUPS: string[] = [
  'fighter-1-fighter-2', // Islam vs Oliveira (already fought)
  'fighter-3-fighter-4', // Gaethje vs Poirier (already fought)
]

/**
 * Get fighter by ID
 */
export function getMockFighter(id: string): Fighter | null {
  return MOCK_FIGHTERS.find((f) => f.id === id) || null
}

/**
 * Get all fighters except the target
 */
export function getMockCandidates(excludeId: string): Fighter[] {
  return MOCK_FIGHTERS.filter((f) => f.id !== excludeId)
}

