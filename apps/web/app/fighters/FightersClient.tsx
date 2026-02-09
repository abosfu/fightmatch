'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import type { WeightClass, FighterWithWeightClass } from '@fightmatch/shared'

interface FightersClientProps {
  weightClasses: WeightClass[]
  initialFighters: FighterWithWeightClass[]
  initialWeightClass?: string
  initialSearch?: string
}

export default function FightersClient({
  weightClasses,
  initialFighters,
  initialWeightClass,
  initialSearch,
}: FightersClientProps) {
  const router = useRouter()
  const [weightClass, setWeightClass] = useState(initialWeightClass || weightClasses[0]?.slug || '')
  const [search, setSearch] = useState(initialSearch || '')
  const [fighters, setFighters] = useState(initialFighters)

  const handleWeightClassChange = (slug: string) => {
    setWeightClass(slug)
    const params = new URLSearchParams()
    params.set('weightClass', slug)
    if (search) params.set('search', search)
    router.push(`/fighters?${params.toString()}`)
  }

  const handleSearchChange = (value: string) => {
    setSearch(value)
    const params = new URLSearchParams()
    if (weightClass) params.set('weightClass', weightClass)
    if (value) params.set('search', value)
    router.push(`/fighters?${params.toString()}`)
  }

  return (
    <>
      <div className="mb-6 flex gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Weight Class
          </label>
          <select
            value={weightClass}
            onChange={(e) => handleWeightClassChange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            {weightClasses.map((wc) => (
              <option key={wc.id} value={wc.slug}>
                {wc.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search
          </label>
          <input
            type="text"
            placeholder="Search fighters..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2"
          />
        </div>
      </div>

      {fighters.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No fighters found</h2>
          <p className="text-gray-600 mb-4">
            {search
              ? `No fighters match "${search}" in this weight class.`
              : 'This weight class doesn\'t have any fighters yet.'}
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
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Weight Class
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stance
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fighters.map((fighter) => (
                <tr key={fighter.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/fighters/${fighter.slug}`}
                      className="text-sm font-medium text-blue-600 hover:text-blue-800"
                    >
                      {fighter.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {fighter.weight_class_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {fighter.stance || 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

