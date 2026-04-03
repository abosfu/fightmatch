import { useState } from "react";

export default function SearchBar({ onSubmit, loading }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    onSubmit(trimmed);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="relative group">
        {/* Glow ring */}
        <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-blue-500/30 via-blue-400/20 to-purple-500/30 opacity-0 group-focus-within:opacity-100 blur-sm transition-opacity duration-500" />

        <div className="relative flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl px-5 py-4 shadow-2xl transition-colors duration-300 group-focus-within:border-blue-500/40 group-focus-within:bg-white/[0.06]">
          {/* Search icon */}
          <svg
            className="h-5 w-5 shrink-0 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
            />
          </svg>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about UFC fighters, bouts, stats..."
            className="flex-1 bg-transparent text-base text-white placeholder:text-slate-500 focus:outline-none"
            disabled={loading}
          />

          {loading ? (
            <div className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
          ) : (
            <kbd className="hidden sm:inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.05] px-2 py-0.5 text-xs text-slate-400">
              <span className="text-[10px]">↵</span> Enter
            </kbd>
          )}
        </div>
      </div>
    </form>
  );
}
