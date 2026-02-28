import Link from 'next/link'
import { dataMode } from '@/lib/data/dataAccess'

export default function Home() {
  const isDemo = dataMode() === 'demo'

  return (
    <div className="min-h-screen p-8">
      {isDemo && (
        <div className="mb-6 rounded-lg bg-amber-50 border border-amber-200 px-4 py-2 text-sm text-amber-800">
          <strong>Demo mode (mock data).</strong>{' '}
          <Link href="/docs/runbook" className="underline">Set up Supabase</Link> for real data.
        </div>
      )}
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">FightMatch</h1>
        <p className="text-gray-600 mb-8">
          Decision-support for UFC matchmaking and rankings: ranked matchup recommendations with explanations and blocked reasons, using constraints and multi-objective scoring.
        </p>
        <div className="grid gap-6 sm:grid-cols-2">
          <Link
            href="/decision/fighter-1"
            className="block p-6 rounded-lg border border-gray-200 bg-white shadow-sm hover:border-blue-300 hover:shadow transition"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Decision Support Demo</h2>
            <p className="text-sm text-gray-500">Ranked recommendations, constraints, and scoring for a fighter.</p>
          </Link>
          <Link
            href="/wc/lightweight"
            className="block p-6 rounded-lg border border-gray-200 bg-white shadow-sm hover:border-blue-300 hover:shadow transition"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Division Dashboards</h2>
            <p className="text-sm text-gray-500">View weight class rankings and fighter metrics.</p>
          </Link>
        </div>
      </div>
    </div>
  )
}

