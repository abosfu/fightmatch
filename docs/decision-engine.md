# Decision Support Engine

The Matchup Decision Engine is a pure TypeScript module that recommends optimal opponent matchups for UFC fighters based on configurable policies and multi-objective scoring.

## Architecture

The engine is located in `apps/web/lib/decision/` and consists of:

- **types.ts**: Domain model (Fighter, Policy, MatchupCandidate, etc.)
- **constraints.ts**: Constraint checking (eligibility rules)
- **scoring.ts**: Multi-objective scoring functions
- **policy.ts**: Policy presets and configuration
- **recommend.ts**: Main recommendation engine
- **mockData.ts**: Mock data for development/testing

## Key Concepts

### Policies

A **Policy** defines how matchups are evaluated. It includes:

1. **Weights**: How much each metric contributes to the total score
2. **Constraints**: Rules that block or warn about certain matchups

**Presets:**
- **Sporting Merit**: Prioritizes competitive fairness and division clarity
- **Business First**: Maximizes hype and revenue potential
- **Balanced**: Balances competitive integrity with business considerations

### Metrics

Five metrics are scored for each matchup (0-1 scale):

1. **Fairness**: Penalizes large rank gaps, rewards adjacent ranks
   - Adjacent ranks (gap=1) = 1.0
   - Exponential decay as gap increases
   - Formula: `1.0 * (0.1^(gap/maxGap))`

2. **Division Health**: Rewards fights that reduce "logjams"
   - Adjacent ranks (gap ≤2) = 1.0
   - Moderate gaps (3-5) = 0.7
   - Large gaps (6-10) = 0.4
   - Very large gaps (>10) = 0.2

3. **Risk**: Penalizes uncertainty (inverted - higher = lower risk)
   - Factors: long layoffs (>12 months = +0.3, >6 months = +0.15)
   - Injury status (+0.2 if injured)
   - Score = `1 - min(1, risk)`

4. **Hype**: Proxy with popularity scores
   - Average of both fighters' popularity (0-100)
   - Normalized to 0-1

5. **Activity**: Rewards active fighters, penalizes long layoffs
   - Ideal: both active within 6 months (180 days)
   - Formula: `(avgScore * 0.7 + compatibility * 0.3)`

### Constraints

Constraints check eligibility and return violations:

1. **same_fighter**: Cannot match a fighter against themselves (blocking)
2. **recent_matchup**: Fighters who fought recently (blocking if policy disallows)
3. **title_fight_eligibility**: Only top 5 can fight champion (blocking if policy requires)
4. **rank_gap_too_high**: Rank gap exceeds policy limit (blocking)
5. **injured_fighter**: Fighter is currently injured (blocking if policy blocks)
6. **inactive_too_long**: Fighter inactive beyond policy limit (warning)

### Scoring Formula

Total score = weighted average of all metrics:

```
total = (
  fairness * weight_fairness +
  divisionHealth * weight_divisionHealth +
  risk * weight_risk +
  hype * weight_hype +
  activity * weight_activity
) / total_weight
```

## Usage

### Basic Example

```typescript
import { recommend, getPolicy, MOCK_DIVISION, MOCK_FIGHTERS } from '@/lib/decision'

const targetFighter = MOCK_FIGHTERS[0]
const candidates = MOCK_FIGHTERS.slice(1)
const policy = getPolicy('Balanced')

const result = recommend(
  targetFighter,
  candidates,
  MOCK_DIVISION,
  policy,
  [] // recent matchups
)

// result.candidates: ranked eligible matchups
// result.blocked: matchups blocked by constraints
```

### Custom Policy

```typescript
import type { Policy } from '@/lib/decision'

const customPolicy: Policy = {
  name: 'Custom',
  description: 'My custom policy',
  weights: {
    fairness: 0.3,
    divisionHealth: 0.2,
    risk: 0.2,
    hype: 0.2,
    activity: 0.1,
  },
  constraints: {
    allowRecentMatchup: false,
    maxRankGap: 5,
    requireTitleEligibility: true,
    blockInjured: true,
    maxDaysInactive: 365,
  },
}
```

## Tuning Policies

### For More Competitive Matchups

- Increase `fairness` weight (0.4-0.5)
- Decrease `maxRankGap` (3-5)
- Set `requireTitleEligibility: true`

### For More Hype/Revenue

- Increase `hype` weight (0.4-0.5)
- Increase `maxRankGap` (7-10)
- Set `allowRecentMatchup: true` (allow rematches)

### For Division Clarity

- Increase `divisionHealth` weight (0.3-0.4)
- Decrease `maxRankGap` (3-5)
- Focus on adjacent rank matchups

## Integration with Supabase

The engine is designed to work with mock data first, then swap in Supabase queries.

### TODO Markers

1. **Fighter Data** (`mockData.ts`):
   ```typescript
   // TODO: Replace with Supabase queries
   // - Get fighters from fighters table
   // - Include metrics from fighter_metrics table
   ```

2. **Recent Matchups** (`recommend.ts`):
   ```typescript
   // TODO: Get from Supabase fights table
   // Query: SELECT fighter_id_1, fighter_id_2 FROM fights
   // WHERE date > NOW() - INTERVAL '6 months'
   ```

3. **Division Context** (`mockData.ts`):
   ```typescript
   // TODO: Get from Supabase
   // - weight_classes table
   // - rankings table for champion
   ```

4. **Injury Status** (`mockData.ts`):
   ```typescript
   // TODO: Get from fighter_metrics or injuries table
   ```

### Migration Steps

1. Create a new file `apps/web/lib/decision/supabaseData.ts`
2. Implement functions that fetch from Supabase:
   - `getFighterFromSupabase(id: string): Promise<Fighter>`
   - `getCandidatesFromSupabase(weightClassId: string, excludeId: string): Promise<Fighter[]>`
   - `getRecentMatchupsFromSupabase(weightClassId: string): Promise<string[]>`
3. Update `recommend.ts` to accept async data fetchers
4. Update UI page to use Supabase data instead of mock data

## Testing

Run tests with:

```bash
cd apps/web
npm run test
```

Tests cover:
- Scoring functions (fairness, activity, hype, risk)
- Constraint checking (all constraint types)
- Policy weight application

## Future Enhancements

- **ML-based scoring**: Replace deterministic metrics with ML model
- **Historical matchup analysis**: Learn from past fight outcomes
- **Injury prediction**: Factor in injury risk based on history
- **Fan sentiment**: Integrate social media sentiment analysis
- **Revenue prediction**: ML model to predict PPV buys/viewership

