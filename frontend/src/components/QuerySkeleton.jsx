export default function QuerySkeleton() {
  return (
    <div className="w-full max-w-4xl mx-auto mt-8 flex flex-col gap-6">
      {/* Explanation skeleton */}
      <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-6 space-y-3">
        <div className="flex items-center gap-2 mb-1">
          <div className="skeleton h-7 w-7 rounded-lg" />
          <div className="skeleton h-4 w-24 rounded" />
        </div>
        <div className="skeleton h-4 w-full rounded" />
        <div className="skeleton h-4 w-5/6 rounded" />
        <div className="skeleton h-4 w-3/4 rounded" />
      </div>

      {/* SQL skeleton */}
      <div className="rounded-2xl border border-white/[0.05] bg-white/[0.02] p-5 space-y-2">
        <div className="skeleton h-3 w-28 rounded mb-3" />
        <div className="skeleton h-3 w-full rounded" />
        <div className="skeleton h-3 w-4/5 rounded" />
      </div>

      {/* Table skeleton */}
      <div className="rounded-2xl border border-white/[0.05] bg-white/[0.02] overflow-hidden">
        <div className="px-5 py-4 border-b border-white/[0.04]">
          <div className="skeleton h-3 w-20 rounded" />
        </div>
        <div className="p-5 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex gap-6">
              <div className="skeleton h-4 w-1/4 rounded" />
              <div className="skeleton h-4 w-1/3 rounded" />
              <div className="skeleton h-4 w-1/5 rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
