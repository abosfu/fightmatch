import { NextResponse } from 'next/server'
import { supabaseServer } from '@/lib/db/supabaseServer'

export async function GET() {
  try {
    // Test database connection by querying counts
    const [fightersResult, fightsResult, eventsResult] = await Promise.allSettled([
      supabaseServer.from('fighters').select('id', { count: 'exact', head: true }),
      supabaseServer.from('fights').select('id', { count: 'exact', head: true }),
      supabaseServer.from('events').select('id', { count: 'exact', head: true }),
    ])

    const fightersCount =
      fightersResult.status === 'fulfilled' ? fightersResult.value.count || 0 : 0
    const fightsCount =
      fightsResult.status === 'fulfilled' ? fightsResult.value.count || 0 : 0
    const eventsCount =
      eventsResult.status === 'fulfilled' ? eventsResult.value.count || 0 : 0

    // Check if we got any errors
    const hasErrors =
      fightersResult.status === 'rejected' ||
      fightsResult.status === 'rejected' ||
      eventsResult.status === 'rejected'

    if (hasErrors) {
      const errors = [
        fightersResult.status === 'rejected' ? fightersResult.reason : null,
        fightsResult.status === 'rejected' ? fightsResult.reason : null,
        eventsResult.status === 'rejected' ? eventsResult.reason : null,
      ]
        .filter(Boolean)
        .map((e: any) => e?.message || String(e))

      return NextResponse.json(
        {
          ok: false,
          db: 'error',
          error: 'Database connection failed',
          details: errors,
        },
        { status: 500 }
      )
    }

    return NextResponse.json({
      ok: true,
      db: 'connected',
      counts: {
        fighters: fightersCount,
        fights: fightsCount,
        events: eventsCount,
      },
    })
  } catch (error: any) {
    console.error('Health check error:', error)
    return NextResponse.json(
      {
        ok: false,
        db: 'error',
        error: error?.message || 'Unknown error',
      },
      { status: 500 }
    )
  }
}

