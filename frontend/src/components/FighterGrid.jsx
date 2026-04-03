const INITIALS_COLORS = [
  "from-blue-500 to-blue-700",
  "from-purple-500 to-purple-700",
  "from-amber-500 to-amber-700",
  "from-emerald-500 to-emerald-700",
  "from-rose-500 to-rose-700",
  "from-cyan-500 to-cyan-700",
  "from-indigo-500 to-indigo-700",
  "from-orange-500 to-orange-700",
];

function hashColor(id) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
  return INITIALS_COLORS[Math.abs(h) % INITIALS_COLORS.length];
}

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function FighterCard({ fighter }) {
  const grad = hashColor(fighter.fighter_id);
  return (
    <div className="group rounded-2xl border border-white/[0.07] bg-white/[0.03] backdrop-blur-md p-4 flex items-center gap-4 hover:bg-white/[0.06] hover:border-white/[0.12] transition-all duration-300 cursor-default">
      <div
        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${grad} text-sm font-bold text-white shadow-lg`}
      >
        {initials(fighter.name)}
      </div>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-white truncate group-hover:text-blue-300 transition-colors">
          {fighter.name}
        </p>
        <p className="text-xs text-slate-500 truncate mt-0.5">
          {[fighter.stance, fighter.height].filter(Boolean).join(" · ") || "UFC Fighter"}
        </p>
      </div>
    </div>
  );
}

function FighterSkeleton() {
  return (
    <div className="rounded-2xl border border-white/[0.05] bg-white/[0.02] p-4 flex items-center gap-4">
      <div className="skeleton h-11 w-11 shrink-0 rounded-xl" />
      <div className="flex-1 space-y-2">
        <div className="skeleton h-4 w-3/4 rounded" />
        <div className="skeleton h-3 w-1/2 rounded" />
      </div>
    </div>
  );
}

export default function FighterGrid({ fighters, loading }) {
  return (
    <section className="w-full max-w-6xl mx-auto mt-16">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/15">
          <svg className="h-4 w-4 text-amber-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-1.053M18 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm-9-3.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
          </svg>
        </div>
        <h2 className="text-lg font-semibold text-white">Discover Fighters</h2>
        {!loading && fighters.length > 0 && (
          <span className="text-xs text-slate-500 ml-1">{fighters.length} loaded</span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {loading
          ? Array.from({ length: 12 }).map((_, i) => <FighterSkeleton key={i} />)
          : fighters.map((f) => <FighterCard key={f.fighter_id} fighter={f} />)}
      </div>
    </section>
  );
}
