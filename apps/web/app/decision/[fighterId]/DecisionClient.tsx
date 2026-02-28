'use client'

import { useState } from 'react'
import type { DecisionResult } from '@/lib/decision/engine'

export default function DecisionClient({
  result,
  jsonPayload,
}: {
  result: DecisionResult
  jsonPayload: object
}) {
  const [assumptionsOpen, setAssumptionsOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(jsonPayload, null, 2))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // ignore
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={copyJson}
          className="px-4 py-2 rounded-md bg-gray-800 text-white text-sm font-medium hover:bg-gray-700"
        >
          {copied ? 'Copied!' : 'Copy JSON'}
        </button>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <button
          type="button"
          onClick={() => setAssumptionsOpen((o) => !o)}
          className="w-full px-4 py-3 text-left bg-gray-50 font-medium text-gray-900 flex justify-between items-center"
        >
          Assumptions &amp; Limits
          <span className="text-gray-500">{assumptionsOpen ? '▼' : '▶'}</span>
        </button>
        {assumptionsOpen && (
          <div className="px-4 py-3 border-t border-gray-200 bg-white text-sm text-gray-700 list-disc list-inside">
            <ul>
              {result.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {result.blocked.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="font-semibold text-red-900 mb-2">Blocked</h2>
          <ul className="text-sm text-red-800 space-y-1">
            {result.blocked.map((b) => (
              <li key={b.opponentId}>
                <strong>{b.opponentName}</strong>: {b.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <h2 className="px-4 py-3 bg-gray-50 font-semibold text-gray-900 border-b border-gray-200">
          Ranked recommendations
        </h2>
        <ul className="divide-y divide-gray-200">
          {result.ranked.map((r, i) => (
            <li key={r.opponent.id} className="px-4 py-3">
              <div className="flex justify-between items-start">
                <div>
                  <span className="font-medium text-gray-900">#{i + 1} {r.opponent.name}</span>
                  {r.opponent.rank != null && (
                    <span className="ml-2 text-gray-500 text-sm">Rank {r.opponent.rank}</span>
                  )}
                  {r.opponent.tier && (
                    <span className="ml-2 text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                      {r.opponent.tier}
                    </span>
                  )}
                </div>
                <span className="font-mono text-sm text-gray-600">
                  score {r.score.total.toFixed(2)}
                </span>
              </div>
              <div className="mt-2 flex gap-4 text-xs text-gray-500">
                <span>competitiveness {r.score.components.competitiveness.toFixed(2)}</span>
                <span>activity {r.score.components.activity.toFixed(2)}</span>
                <span>excitement {r.score.components.excitement.toFixed(2)}</span>
                <span>risk {r.score.components.risk.toFixed(2)}</span>
              </div>
              {r.score.explanation.why.length > 0 && (
                <div className="mt-1 text-xs text-green-700">
                  Why: {r.score.explanation.why.join(' ')}
                </div>
              )}
              {r.score.explanation.risks.length > 0 && (
                <div className="mt-0.5 text-xs text-amber-700">
                  Risks: {r.score.explanation.risks.join(' ')}
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
