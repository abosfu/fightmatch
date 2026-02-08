import { NextResponse } from 'next/server'
import { getFighterBySlug, getFighterById } from '@/lib/db/queries'

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const fighter = await getFighterById(params.id) || await getFighterBySlug(params.id)
    
    if (!fighter) {
      return NextResponse.json({ error: 'Fighter not found' }, { status: 404 })
    }

    return NextResponse.json(fighter)
  } catch (error) {
    console.error('Error fetching fighter:', error)
    return NextResponse.json({ error: 'Failed to fetch fighter' }, { status: 500 })
  }
}

