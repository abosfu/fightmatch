import { getWeightClasses, getFightersByWeightClass, getWeightClassBySlug } from '@/lib/db/queries'
import FightersClient from './FightersClient'

export default async function FightersPage({
  searchParams,
}: {
  searchParams: { weightClass?: string; search?: string }
}) {
  let weightClasses
  try {
    weightClasses = await getWeightClasses()
  } catch (error) {
    console.error('Error fetching weight classes:', error)
    weightClasses = []
  }

  const selectedWeightClass = searchParams.weightClass || weightClasses[0]?.slug

  let fighters: any[] = []
  if (selectedWeightClass) {
    try {
      const wc = await getWeightClassBySlug(selectedWeightClass)
      if (wc) {
        fighters = await getFightersByWeightClass(wc.id, searchParams.search)
      }
    } catch (error) {
      console.error('Error fetching fighters:', error)
      fighters = []
    }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Fighters Directory</h1>
        <FightersClient
          weightClasses={weightClasses}
          initialFighters={fighters}
          initialWeightClass={selectedWeightClass}
          initialSearch={searchParams.search}
        />
      </div>
    </div>
  )
}

