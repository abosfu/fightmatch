import { NextResponse } from 'next/server'
import { supabaseServer } from '@/lib/db/supabaseServer'
import { dataMode } from '@/lib/data/dataMode'
import { getWeightClassBySlug, getRankingEntriesWithFighters } from '@/lib/data/dataAccess'

export async function GET(request: Request) {
  try {
    // MVP admin gate
    const authHeader = request.headers.get('authorization')
    const adminSecret = process.env.ADMIN_SECRET

    if (!adminSecret || authHeader !== `Bearer ${adminSecret}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const weightClassSlug = searchParams.get('weightClassSlug')

    if (!weightClassSlug) {
      return NextResponse.json({ error: 'weightClassSlug is required' }, { status: 400 })
    }

    const weightClass = await getWeightClassBySlug(weightClassSlug)
    if (!weightClass) {
      return NextResponse.json({ error: 'Weight class not found' }, { status: 404 })
    }

    const rankings = await getRankingEntriesWithFighters(weightClass.id)
    return NextResponse.json(rankings)
  } catch (error) {
    console.error('Error fetching rankings:', error)
    return NextResponse.json({ error: 'Failed to fetch rankings' }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    // MVP admin gate
    const authHeader = request.headers.get('authorization')
    const adminSecret = process.env.ADMIN_SECRET

    if (!adminSecret || authHeader !== `Bearer ${adminSecret}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()
    
    // Handle test authentication request
    if (body.test) {
      return NextResponse.json({ success: true, authenticated: true })
    }

    if (dataMode() === 'demo') {
      return NextResponse.json(
        { error: 'Admin write requires Supabase; use runbook to configure.' },
        { status: 403 }
      )
    }

    const { weightClassSlug, entries } = body

    if (!weightClassSlug || !Array.isArray(entries)) {
      return NextResponse.json(
        { error: 'weightClassSlug and entries array are required' },
        { status: 400 }
      )
    }

    const weightClass = await getWeightClassBySlug(weightClassSlug)
    if (!weightClass) {
      return NextResponse.json({ error: 'Weight class not found' }, { status: 404 })
    }

    // Get or create latest ranking
    const { data: existingRanking } = await supabaseServer
      .from('rankings')
      .select('id')
      .eq('weight_class_id', weightClass.id)
      .order('snapshot_date', { ascending: false })
      .limit(1)
      .single()

    let rankingId = existingRanking?.id

    if (!rankingId) {
      const { data: newRanking, error: rankingError } = await supabaseServer
        .from('rankings')
        .insert({
          weight_class_id: weightClass.id,
          snapshot_date: new Date().toISOString().split('T')[0],
        })
        .select('id')
        .single()

      if (rankingError) throw rankingError
      rankingId = newRanking.id
    }

    // Upsert ranking entries
    const upsertData = entries.map((entry: any) => ({
      ranking_id: rankingId,
      fighter_id: entry.fighterId,
      rank: entry.rank,
      tier: entry.tier || null,
    }))

    const { error: upsertError } = await supabaseServer
      .from('ranking_entries')
      .upsert(upsertData, {
        onConflict: 'ranking_id,fighter_id',
      })

    if (upsertError) throw upsertError

    return NextResponse.json({ success: true, rankingId })
  } catch (error) {
    console.error('Error upserting rankings:', error)
    return NextResponse.json({ error: 'Failed to upsert rankings' }, { status: 500 })
  }
}
