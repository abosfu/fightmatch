import { NextResponse } from 'next/server'
import { getWeightClasses } from '@/lib/data/dataAccess'

export async function GET() {
  try {
    const weightClasses = await getWeightClasses()
    return NextResponse.json(weightClasses)
  } catch (error) {
    console.error('Error fetching weight classes:', error)
    return NextResponse.json({ error: 'Failed to fetch weight classes' }, { status: 500 })
  }
}

