import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

/**
 * Thin API that calls the Python matchmaking engine (recommend) and returns
 * ranked candidates with p_win, constraints_passed/failed, score_components.
 * Requires: DATABASE_URL and trained model at repo root models/lightgbm.joblib.
 * Run from repo root: python -m modeling recommend --fighter_id X --weight_class Y
 * (with PYTHONPATH=services/modeling)
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const fighterId = searchParams.get('fighter_id')
    const weightClass = searchParams.get('weight_class')

    if (!fighterId || !weightClass) {
      return NextResponse.json(
        { error: 'fighter_id and weight_class are required' },
        { status: 400 }
      )
    }

    const cwd = process.cwd()
    const repoRoot = cwd.endsWith('apps/web') || cwd.endsWith('web') ? path.resolve(cwd, '..', '..') : cwd
    const modelingDir = path.join(repoRoot, 'services', 'modeling')
    const pythonPath = process.env.PYTHON_PATH || 'python3'

    const result = await new Promise<string>((resolve, reject) => {
      const proc = spawn(
        pythonPath,
        [
          '-m', 'modeling',
          'recommend',
          '--fighter_id', fighterId,
          '--weight_class', weightClass,
        ],
        {
          cwd: modelingDir,
          env: { ...process.env, PYTHONPATH: modelingDir, DATABASE_URL: process.env.DATABASE_URL || '' },
        }
      )
      let out = ''
      let err = ''
      proc.stdout?.on('data', (d) => { out += d.toString() })
      proc.stderr?.on('data', (d) => { err += d.toString() })
      proc.on('close', (code) => {
        if (code !== 0) reject(new Error(err || `exit ${code}`))
        else resolve(out)
      })
    })

    const json = JSON.parse(result.trim())
    return NextResponse.json(json)
  } catch (e: any) {
    console.error('Matchmaking API error:', e)
    return NextResponse.json(
      { error: 'Matchmaking failed', details: e?.message },
      { status: 502 }
    )
  }
}
