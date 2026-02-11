/**
 * Policy presets for matchup recommendations
 * Each policy has different weights and constraint strictness
 */

import type { Policy } from './types'

export const POLICY_PRESETS: Record<string, Policy> = {
  'Sporting Merit': {
    name: 'Sporting Merit',
    description: 'Prioritize competitive fairness and division clarity',
    weights: {
      fairness: 0.4,
      divisionHealth: 0.3,
      risk: 0.2,
      hype: 0.05,
      activity: 0.05,
    },
    constraints: {
      allowRecentMatchup: false,
      maxRankGap: 5,
      requireTitleEligibility: true,
      blockInjured: true,
      maxDaysInactive: 365,
    },
  },
  'Business First': {
    name: 'Business First',
    description: 'Maximize hype and revenue potential',
    weights: {
      fairness: 0.15,
      divisionHealth: 0.1,
      risk: 0.15,
      hype: 0.5,
      activity: 0.1,
    },
    constraints: {
      allowRecentMatchup: true, // Allow rematches if they're big draws
      maxRankGap: 10, // More flexible on rank gaps
      requireTitleEligibility: false,
      blockInjured: true,
      maxDaysInactive: 540, // Allow longer layoffs
    },
  },
  Balanced: {
    name: 'Balanced',
    description: 'Balance competitive integrity with business considerations',
    weights: {
      fairness: 0.25,
      divisionHealth: 0.2,
      risk: 0.2,
      hype: 0.2,
      activity: 0.15,
    },
    constraints: {
      allowRecentMatchup: false,
      maxRankGap: 7,
      requireTitleEligibility: true,
      blockInjured: true,
      maxDaysInactive: 450,
    },
  },
}

export function getPolicy(name: string): Policy {
  return POLICY_PRESETS[name] || POLICY_PRESETS['Balanced']
}

export function getPolicyNames(): string[] {
  return Object.keys(POLICY_PRESETS)
}

