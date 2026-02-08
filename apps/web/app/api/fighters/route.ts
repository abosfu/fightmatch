import { NextResponse } from 'next/server'
import { getFightersByWeightClass, getWeightClassBySlug } from '@/lib/db/queries'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const weightClassSlug = searchParams.get('weightClassId') || searchParams.get('weightClass')
    const search = searchParams.get('search')

    if (!weightClassSlug) {
      return NextResponse.json({ error: 'weightClassId is required' }, { status: 400 })
    }

    const weightClass = await getWeightClassBySlug(weightClassSlug)
    if (!weightClass) {
      return NextResponse.json({ error: 'Weight class not found' }, { status: 404 })
    }

    const fighters = await getFightersByWeightClass(weightClass.id, search || undefined)
    return NextResponse.json(fighters)
  } catch (error) {
    console.error('Error fetching fighters:', error)
    return NextResponse.json({ error: 'Failed to fetch fighters' }, { status: 500 })
  }
}

