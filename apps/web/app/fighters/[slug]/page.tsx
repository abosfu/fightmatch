import { notFound } from 'next/navigation'
import Link from 'next/link'
import {
  getFighterBySlug,
  getFighterMetrics,
  getFighterRecentFights,
  getFighterPrimaryWeightClass,
} from '@/lib/data/dataAccess'

export default async function FighterPage({
  params,
}: {
  params: { slug: string }
}) {
  let fighter
  try {
    fighter = await getFighterBySlug(params.slug)
  } catch (error) {
    console.error('Error fetching fighter:', error)
    notFound()
  }

  if (!fighter) {
    notFound()
  }

  // Get primary weight class
  let weightClass
  try {
    weightClass = await getFighterPrimaryWeightClass(fighter.id)
  } catch (error) {
    console.error('Error fetching weight class:', error)
    weightClass = null
  }
  const weightClassId = weightClass?.id || ''

  let metrics = null
  if (weightClassId) {
    try {
      metrics = await getFighterMetrics(fighter.id, weightClassId)
    } catch (error) {
      console.error('Error fetching metrics:', error)
    }
  }

  let recentFights = []
  try {
    recentFights = await getFighterRecentFights(fighter.id, 5)
  } catch (error) {
    console.error('Error fetching recent fights:', error)
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <Link
            href="/fighters"
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            ← Back to Fighters Directory
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h1 className="text-3xl font-bold mb-4">{fighter.name}</h1>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <div className="text-sm text-gray-500">Height</div>
              <div className="text-lg font-semibold">
                {fighter.height_inches ? `${fighter.height_inches}"` : 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Reach</div>
              <div className="text-lg font-semibold">
                {fighter.reach_inches ? `${fighter.reach_inches}"` : 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Stance</div>
              <div className="text-lg font-semibold">{fighter.stance || 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Date of Birth</div>
              <div className="text-lg font-semibold">
                {fighter.date_of_birth
                  ? new Date(fighter.date_of_birth).toLocaleDateString()
                  : 'N/A'}
              </div>
            </div>
          </div>

          {metrics && (
            <div className="border-t pt-4">
              <h2 className="text-xl font-semibold mb-4">Metrics</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Last Fight</div>
                  <div className="text-lg font-semibold">
                    {metrics.last_fight_date
                      ? new Date(metrics.last_fight_date).toLocaleDateString()
                      : 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Days Since Fight</div>
                  <div className="text-lg font-semibold">
                    {metrics.days_since_fight ?? 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Win Streak</div>
                  <div className="text-lg font-semibold">{metrics.win_streak}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Finish Rate</div>
                  <div className="text-lg font-semibold">
                    {metrics.finish_rate
                      ? `${Math.round(metrics.finish_rate * 100)}%`
                      : 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Record</div>
                  <div className="text-lg font-semibold">
                    {metrics.wins}-{metrics.losses}
                    {metrics.draws > 0 && `-${metrics.draws}`}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6">
            <Link
              href={`/recommend?fighterId=${fighter.id}`}
              className="inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium"
            >
              Recommend Opponents
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Fights</h2>
          <div className="space-y-4">
            {recentFights.length === 0 ? (
              <p className="text-gray-500">No recent fights found.</p>
            ) : (
              recentFights.map((fight) => {
                const opponent = fight.participants.find((p) => p.fighter.id !== fighter.id)
                const result = fight.participants.find((p) => p.fighter.id === fighter.id)

                return (
                  <div key={fight.id} className="border-b pb-4 last:border-b-0">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-semibold">
                          vs. {opponent?.fighter.name || 'Unknown'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(fight.date).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="text-right">
                        {result?.is_winner !== null && (
                          <span
                            className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              result?.is_winner
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {result?.is_winner ? 'Win' : 'Loss'}
                          </span>
                        )}
                        <div className="text-sm text-gray-500 mt-1">
                          {fight.result_method} {fight.result_round && `(R${fight.result_round})`}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

