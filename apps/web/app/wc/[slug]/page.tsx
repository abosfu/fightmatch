import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getWeightClassBySlug, getRankingEntriesWithFighters } from '@/lib/data/dataAccess'

export default async function WeightClassPage({
  params,
}: {
  params: { slug: string }
}) {
  const weightClass = await getWeightClassBySlug(params.slug)
  if (!weightClass) {
    notFound()
  }

  let rankings
  try {
    rankings = await getRankingEntriesWithFighters(weightClass.id)
  } catch (error) {
    console.error('Error fetching rankings:', error)
    rankings = []
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">{weightClass.name}</h1>
        <p className="text-gray-600 mb-6">
          Weight Limit: {weightClass.weight_limit_lbs ? `${weightClass.weight_limit_lbs} lbs` : 'N/A'}
        </p>

        {rankings.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No fighters found</h2>
            <p className="text-gray-600 mb-4">
              This weight class doesn&apos;t have any ranked fighters yet.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              To load data, follow the setup instructions in{' '}
              <a
                href="/docs/runbook.md"
                className="text-blue-600 hover:text-blue-800 underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                docs/runbook.md
              </a>
            </p>
            <Link
              href="/fighters"
              className="inline-block text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              ← Back to Fighters Directory
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tier
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Fight
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Streak
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Finish Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Days Since Fight
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {rankings.map((entry) => {
                const metrics = entry.metrics
                const lastFightDate = metrics?.last_fight_date
                  ? new Date(metrics.last_fight_date).toLocaleDateString()
                  : 'N/A'
                const streak = metrics
                  ? metrics.win_streak > 0
                    ? `W${metrics.win_streak}`
                    : metrics.loss_streak > 0
                    ? `L${metrics.loss_streak}`
                    : '-'
                  : '-'
                const finishRate = metrics?.finish_rate
                  ? `${Math.round(metrics.finish_rate * 100)}%`
                  : 'N/A'
                const daysSince = metrics?.days_since_fight ?? null

                return (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {entry.rank}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/fighters/${entry.fighter.slug}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        {entry.fighter.name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        {entry.tier || 'Unranked'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lastFightDate}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {streak}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {finishRate}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {daysSince !== null ? daysSince : 'N/A'}
                    </td>
                  </tr>
                )
                })}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-6">
          <Link
            href="/fighters"
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            ← Back to Fighters Directory
          </Link>
        </div>
      </div>
    </div>
  )
}

