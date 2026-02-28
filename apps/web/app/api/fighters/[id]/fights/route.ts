import { NextResponse } from 'next/server'
import { getFighterRecentFights, getFighterById, getFighterBySlug } from '@/lib/data/dataAccess'

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '5', 10)

    const fighter = await getFighterById(params.id) || await getFighterBySlug(params.id)
    if (!fighter) {
      return NextResponse.json({ error: 'Fighter not found' }, { status: 404 })
    }

    const fights = await getFighterRecentFights(fighter.id, limit)
    return NextResponse.json(fights)
  } catch (error) {
    console.error('Error fetching fights:', error)
    return NextResponse.json({ error: 'Failed to fetch fights' }, { status: 500 })
  }
}

