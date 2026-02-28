import Link from 'next/link'

export default function RunbookPage() {
  return (
    <div className="min-h-screen p-8 max-w-2xl mx-auto">
      <Link href="/" className="text-blue-600 hover:text-blue-800 text-sm font-medium mb-6 inline-block">
        ← Home
      </Link>
      <h1 className="text-2xl font-bold mb-4">Supabase setup</h1>
      <p className="text-gray-600 mb-4">
        To run FightMatch with real data, configure Supabase and environment variables.
      </p>
      <ol className="list-decimal list-inside space-y-2 text-gray-700">
        <li>Create a Supabase project at supabase.com</li>
        <li>Run <code className="bg-gray-100 px-1">supabase/migrations/0001_init.sql</code> in the SQL Editor</li>
        <li>Load <code className="bg-gray-100 px-1">supabase/seed.sql</code></li>
        <li>Create <code className="bg-gray-100 px-1">apps/web/.env.local</code> with <code className="bg-gray-100 px-1">NEXT_PUBLIC_SUPABASE_URL</code>, <code className="bg-gray-100 px-1">NEXT_PUBLIC_SUPABASE_ANON_KEY</code>, and <code className="bg-gray-100 px-1">SUPABASE_SERVICE_ROLE_KEY</code></li>
        <li>Restart the dev server</li>
      </ol>
      <p className="mt-6 text-sm text-gray-500">
        Full step-by-step instructions are in <code>docs/runbook.md</code> in the repository.
      </p>
    </div>
  )
}
