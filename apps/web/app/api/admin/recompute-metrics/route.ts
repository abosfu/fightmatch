import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    // MVP admin gate
    const authHeader = request.headers.get('authorization')
    const adminSecret = process.env.ADMIN_SECRET

    if (!adminSecret || authHeader !== `Bearer ${adminSecret}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Stub implementation - document how to wire this
    // This would:
    // 1. Query all fighters
    // 2. For each fighter, compute:
    //    - last_fight_date from fight_participants
    //    - days_since_fight
    //    - win_streak / loss_streak from recent fights
    //    - finish_rate from wins by finish / total wins
    //    - total_fights, wins, losses, etc.
    // 3. Upsert into fighter_metrics table

    return NextResponse.json({
      success: true,
      message: 'Metrics recomputation is a stub. See route implementation for details.',
    })
  } catch (error) {
    console.error('Error recomputing metrics:', error)
    return NextResponse.json({ error: 'Failed to recompute metrics' }, { status: 500 })
  }
}

