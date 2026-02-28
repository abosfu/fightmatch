import Link from 'next/link'
import { notFound } from 'next/navigation'
import { runDecision } from '@/lib/decision/engine'
import { dataMode } from '@/lib/data/dataAccess'
import DecisionClient from './DecisionClient'

export default async function DecisionPage({
  params,
}: {
  params: { fighterId: string }
}) {
  const result = await runDecision(params.fighterId)
  if (!result) notFound()

  const isDemo = dataMode() === 'demo'
  const jsonPayload = {
    fighterId: result.fighterId,
    fighterName: result.fighterName,
    weightClassName: result.weightClassName,
    ranked: result.ranked.map((r) => ({
      opponent: { id: r.opponent.id, name: r.opponent.name, rank: r.opponent.rank, tier: r.opponent.tier },
      score: r.score.total,
      components: r.score.components,
      why: r.score.explanation.why,
      risks: r.score.explanation.risks,
    })),
    blocked: result.blocked,
    assumptions: result.assumptions,
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        {isDemo && (
          <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 px-4 py-2 text-sm text-amber-800">
            <strong>Demo mode (mock data).</strong>{' '}
            <Link href="/docs/runbook" className="underline">Set up Supabase</Link> for real data.
          </div>
        )}
        <div className="mb-6">
          <Link href="/" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            ← Home
          </Link>
        </div>
        <h1 className="text-3xl font-bold mb-2">Decision Support: {result.fighterName}</h1>
        <p className="text-gray-600 mb-6">{result.weightClassName}</p>
        <DecisionClient
          result={result}
          jsonPayload={jsonPayload}
        />
      </div>
    </div>
  )
}
