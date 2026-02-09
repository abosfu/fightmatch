'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import type { RecommendationResult } from '@fightmatch/shared'

export default function RecommendPage() {
  const [fighterId, setFighterId] = useState('')
  const [fighterName, setFighterName] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [recommendations, setRecommendations] = useState<RecommendationResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (searchQuery.length > 2) {
      const timer = setTimeout(() => {
        fetch(`/api/fighters?search=${encodeURIComponent(searchQuery)}`)
          .then((res) => {
            if (!res.ok) {
              throw new Error('Failed to search fighters')
            }
            return res.json()
          })
          .then((data) => {
            if (Array.isArray(data)) {
              setSearchResults(data.slice(0, 5))
            } else {
              setSearchResults([])
            }
          })
          .catch((err) => {
            console.error('Error searching fighters:', err)
            setSearchResults([])
          })
      }, 300)

      return () => clearTimeout(timer)
    } else {
      setSearchResults([])
    }
  }, [searchQuery])

  const handleSearch = async () => {
    if (!fighterId) return

    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/recommendations?fighterId=${fighterId}`)
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.error || 'Failed to fetch recommendations')
      }
      const data = await res.json()
      if (Array.isArray(data)) {
        setRecommendations(data)
      } else {
        setRecommendations([])
        setError('No recommendations available')
      }
    } catch (error: any) {
      console.error('Error fetching recommendations:', error)
      setError(error?.message || 'Failed to fetch recommendations. Please try again.')
      setRecommendations([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Opponent Recommendations</h1>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Fighter
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Search for a fighter..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
              {searchResults.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
                  {searchResults.map((fighter) => (
                    <button
                      key={fighter.id}
                      onClick={() => {
                        setFighterId(fighter.id)
                        setFighterName(fighter.name)
                        setSearchQuery(fighter.name)
                        setSearchResults([])
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100"
                    >
                      {fighter.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {fighterName && (
              <div className="mt-2 text-sm text-gray-600">Selected: {fighterName}</div>
            )}
          </div>

          <button
            onClick={handleSearch}
            disabled={!fighterId || loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading...' : 'Get Recommendations'}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 text-sm">{error}</p>
            <p className="text-red-600 text-xs mt-2">
              Make sure the database is set up correctly. See{' '}
              <a
                href="/docs/runbook.md"
                className="underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                docs/runbook.md
              </a>{' '}
              for setup instructions.
            </p>
          </div>
        )}

        {recommendations.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold mb-4">Top 5 Recommendations</h2>
            {recommendations.map((rec, idx) => (
              <div
                key={rec.opponent.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold">
                      #{idx + 1} - {rec.opponent.name}
                    </h3>
                    {rec.opponent.rank && (
                      <p className="text-sm text-gray-500">Rank: #{rec.opponent.rank}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">
                      {rec.score.total.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500">Total Score</div>
                  </div>
                </div>

                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Score Breakdown</h4>
                  <div className="space-y-2">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span>Competitiveness</span>
                        <span>{rec.score.components.competitiveness.toFixed(2)}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${rec.score.components.competitiveness * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span>Activity</span>
                        <span>{rec.score.components.activity.toFixed(2)}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${rec.score.components.activity * 100}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span>Excitement</span>
                        <span>{rec.score.components.excitement.toFixed(2)}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-yellow-600 h-2 rounded-full"
                          style={{ width: `${rec.score.components.excitement * 100}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span>Risk (inverted)</span>
                        <span>{rec.score.components.risk.toFixed(2)}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-red-600 h-2 rounded-full"
                          style={{ width: `${rec.score.components.risk * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Why it makes sense</h4>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {rec.score.explanation.why.map((reason, i) => (
                        <li key={i}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">What could go wrong</h4>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {rec.score.explanation.risks.map((risk, i) => (
                        <li key={i}>{risk}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="mt-4">
                  <Link
                    href={`/fighters/${rec.opponent.slug}`}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    View Fighter Profile →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && !error && recommendations.length === 0 && fighterId && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No recommendations found</h2>
            <p className="text-gray-600 mb-4">
              No suitable opponents found for {fighterName || 'this fighter'}.
            </p>
            <p className="text-sm text-gray-500">
              This may happen if there are no other fighters in the same weight class.
            </p>
          </div>
        )}

        {!loading && !fighterId && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Select a fighter</h2>
            <p className="text-gray-600">
              Search for a fighter above to get opponent recommendations.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

