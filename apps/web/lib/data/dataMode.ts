export type DataMode = 'demo' | 'supabase'

export function dataMode(): DataMode {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY
  return url && key ? 'supabase' : 'demo'
}
