'use client'

import { useState, useEffect } from 'react'
import type { WeightClass, RankingEntryWithFighter } from '@fightmatch/shared'

export default function AdminRankingsPage() {
  const [weightClasses, setWeightClasses] = useState<WeightClass[]>([])
  const [selectedWeightClass, setSelectedWeightClass] = useState<string>('')
  const [rankings, setRankings] = useState<RankingEntryWithFighter[]>([])
  const [adminSecret, setAdminSecret] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    fetch('/api/weight-classes')
      .then((res) => res.json())
      .then((data) => {
        setWeightClasses(data)
        if (data.length > 0) {
          setSelectedWeightClass(data[0].slug)
        }
      })
      .catch(console.error)
  }, [])

  useEffect(() => {
    if (selectedWeightClass && isAuthenticated && adminSecret) {
      fetch(`/api/admin/rankings?weightClassSlug=${selectedWeightClass}`, {
        headers: {
          Authorization: `Bearer ${adminSecret}`,
        },
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.error) {
            console.error(data.error)
          } else {
            setRankings(data)
          }
        })
        .catch(console.error)
    }
  }, [selectedWeightClass, isAuthenticated, adminSecret])

  const handleAuth = async () => {
    // In MVP, verify secret via API
    // In production, this would be a proper auth check
    try {
      const res = await fetch('/api/admin/rankings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${adminSecret}`,
        },
        body: JSON.stringify({ test: true }),
      })
      
      if (res.status === 401) {
        alert('Invalid admin secret')
      } else {
        setIsAuthenticated(true)
      }
    } catch (error) {
      // For MVP, just set authenticated if secret is provided
      // Real auth check happens on API side
      if (adminSecret) {
        setIsAuthenticated(true)
      }
    }
  }

  const handleSave = async () => {
    if (!isAuthenticated || !selectedWeightClass) return

    // Collect ranking data from form
    const entries = rankings.map((entry, idx) => ({
      fighterId: entry.fighter_id,
      rank: idx + 1,
      tier: entry.tier || null,
    }))

    try {
      const res = await fetch('/api/admin/rankings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${adminSecret}`,
        },
        body: JSON.stringify({
          weightClassSlug: selectedWeightClass,
          entries,
        }),
      })

      if (res.ok) {
        alert('Rankings saved successfully')
      } else {
        alert('Failed to save rankings')
      }
    } catch (error) {
      console.error('Error saving rankings:', error)
      alert('Error saving rankings')
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-md mx-auto">
          <h1 className="text-2xl font-bold mb-4">Admin Access</h1>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Admin Secret
            </label>
            <input
              type="password"
              value={adminSecret}
              onChange={(e) => setAdminSecret(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 mb-4"
            />
            <button
              onClick={handleAuth}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium"
            >
              Authenticate
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Admin: Rankings Editor</h1>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Weight Class
          </label>
          <select
            value={selectedWeightClass}
            onChange={(e) => setSelectedWeightClass(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            {weightClasses.map((wc) => (
              <option key={wc.id} value={wc.slug}>
                {wc.name}
              </option>
            ))}
          </select>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <p className="text-gray-600 mb-4">
            Ranking editor interface. In MVP, this is a simplified version. Full implementation
            would allow drag-and-drop reordering and tier assignment.
          </p>
          <button
            onClick={handleSave}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium"
          >
            Save Rankings
          </button>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fighter
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tier
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rankings.map((entry) => (
                <tr key={entry.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {entry.rank}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {entry.fighter.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                      {entry.tier || 'Unranked'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

