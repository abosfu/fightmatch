import { NextResponse } from 'next/server'
import { getHealth } from '@/lib/data/dataAccess'

export async function GET() {
  try {
    const result = await getHealth()
    if (result.ok) return NextResponse.json(result)
    return NextResponse.json(result, { status: 500 })
  } catch (error: any) {
    console.error('Health check error:', error)
    return NextResponse.json(
      { ok: false, db: 'error', error: error?.message || 'Unknown error' },
      { status: 500 }
    )
  }
}

