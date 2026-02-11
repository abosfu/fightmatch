'use client'

import { useState, useEffect } from 'react'
import {
  getMockFighter,
  getMockCandidates,
  MOCK_DIVISION,
  MOCK_RECENT_MATCHUPS,
  getPolicy,
  getPolicyNames,
  recommend,
} from '@/lib/decision'
import type { RecommendationResult, MatchupCandidate } from '@/lib/decision'

export default function DecisionPage({ params }: { params: { fighterId: string } }) {
  const [targetFighter, setTargetFighter] = useState(
    getMockFighter(params.fighterId)
  )
  const [selectedPolicy, setSelectedPolicy] = useState('Balanced')
  const [result, setResult] = useState<RecommendationResult | null>(null)

  useEffect(() => {
    if (!targetFighter) return

    const candidates = getMockCandidates(targetFighter.id)
    const policy = getPolicy(selectedPolicy)
    const recommendation = recommend(
      targetFighter,
      candidates,
      MOCK_DIVISION,
      policy,
      MOCK_RECENT_MATCHUPS
    )

    setResult(recommendation)
  }, [targetFighter, selectedPolicy])

  if (!targetFighter) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-red-900 mb-2">Fighter not found</h2>
            <p className="text-red-700">
              Fighter with ID "{params.fighterId}" not found in mock data.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Matchup Decision Engine</h1>

        {/* Target Fighter Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Target Fighter</h2>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="text-2xl font-bold">{targetFighter.name}</div>
              <div className="text-sm text-gray-600 mt-1">
                Rank #{targetFighter.rank}
                {targetFighter.isChampion && (
                  <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">
                    Champion
                  </span>
                )}
                {targetFighter.isInjured && (
                  <span className="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
                    Injured
                  </span>
                )}
              </div>
            </div>
            <div className="text-right text-sm text-gray-600">
              <div>Last Fight: {targetFighter.lastFightDate?.toLocaleDateString() || 'N/A'}</div>
              <div>Popularity: {targetFighter.popularityScore}/100</div>
            </div>
          </div>
        </div>

        {/* Policy Selector */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Policy Preset
          </label>
          <select
            value={selectedPolicy}
            onChange={(e) => setSelectedPolicy(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 w-full max-w-md"
          >
            {getPolicyNames().map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          {result && (
            <p className="text-sm text-gray-600 mt-2">
              {result.policy.description}
            </p>
          )}
        </div>

        {/* Recommendations */}
        {result && (
          <>
            {/* Top Candidates */}
            <div className="mb-6">
              <h2 className="text-2xl font-semibold mb-4">Top Recommendations</h2>
              <div className="space-y-4">
                {result.candidates.slice(0, 5).map((candidate, idx) => (
                  <CandidateCard
                    key={candidate.fighter.id}
                    candidate={candidate}
                    rank={idx + 1}
                    policy={result.policy}
                  />
                ))}
                {result.candidates.length === 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                    <p className="text-yellow-800">
                      No eligible candidates found with current policy constraints.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Blocked Candidates */}
            {result.blocked.length > 0 && (
              <div className="mb-6">
                <h2 className="text-2xl font-semibold mb-4 text-red-700">
                  Blocked Candidates
                </h2>
                <div className="space-y-4">
                  {result.blocked.map((candidate) => (
                    <CandidateCard
                      key={candidate.fighter.id}
                      candidate={candidate}
                      rank={null}
                      isBlocked={true}
                      policy={result.policy}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function CandidateCard({
  candidate,
  rank,
  isBlocked = false,
  policy,
}: {
  candidate: MatchupCandidate
  rank: number | null
  isBlocked?: boolean
  policy?: any
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border ${
        isBlocked ? 'border-red-200 bg-red-50' : 'border-gray-200'
      } p-6`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            {rank !== null && (
              <div className="text-2xl font-bold text-gray-400">#{rank}</div>
            )}
            <div>
              <div className="text-xl font-semibold">{candidate.fighter.name}</div>
              <div className="text-sm text-gray-600">
                Rank #{candidate.fighter.rank}
                {candidate.fighter.isChampion && (
                  <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">
                    Champion
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="mt-2">
            <div className="text-sm text-gray-700">{candidate.explanation}</div>
          </div>
          {candidate.violations.length > 0 && (
            <div className="mt-3">
              {candidate.violations.map((violation, idx) => (
                <div
                  key={idx}
                  className={`text-xs px-2 py-1 rounded mb-1 ${
                    violation.severity === 'blocking'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {violation.reason}
                </div>
              )))}
            </div>
          )}
        </div>
        <div className="text-right ml-4">
          <div className="text-3xl font-bold text-blue-600">
            {candidate.totalScore.toFixed(2)}
          </div>
          <div className="text-xs text-gray-500">Total Score</div>
        </div>
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        {expanded ? 'Hide' : 'View'} Breakdown →
      </button>

      {expanded && (
        <div className="mt-4 pt-4 border-t">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Score Breakdown</h4>
          <div className="space-y-3">
            <MetricBar
              label="Fairness"
              score={candidate.breakdown.fairness}
              weight={policy?.weights.fairness || 0}
            />
            <MetricBar
              label="Division Health"
              score={candidate.breakdown.divisionHealth}
              weight={policy?.weights.divisionHealth || 0}
            />
            <MetricBar
              label="Risk (inverted)"
              score={candidate.breakdown.risk}
              weight={policy?.weights.risk || 0}
            />
            <MetricBar
              label="Hype"
              score={candidate.breakdown.hype}
              weight={policy?.weights.hype || 0}
            />
            <MetricBar
              label="Activity"
              score={candidate.breakdown.activity}
              weight={policy?.weights.activity || 0}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function MetricBar({
  label,
  score,
  weight,
}: {
  label: string
  score: number
  weight: number
}) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="text-gray-500">
          {score.toFixed(2)} (weight: {weight.toFixed(2)})
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full"
          style={{ width: `${score * 100}%` }}
        />
      </div>
    </div>
  )
}

