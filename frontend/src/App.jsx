import { useEffect, useState } from "react";
import SearchBar from "./components/SearchBar";
import QueryResult from "./components/QueryResult";
import QuerySkeleton from "./components/QuerySkeleton";
import FighterGrid from "./components/FighterGrid";

const API = "/api";

export default function App() {
  const [fighters, setFighters] = useState([]);
  const [fightersLoading, setFightersLoading] = useState(true);

  const [queryLoading, setQueryLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Fetch fighters on mount
  useEffect(() => {
    fetch(`${API}/fighters`)
      .then((r) => r.json())
      .then(setFighters)
      .catch(() => {})
      .finally(() => setFightersLoading(false));
  }, []);

  const handleQuery = async (question) => {
    setQueryLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await fetch(`${API}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `Request failed (${res.status})`);
      }
      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="min-h-screen px-4 sm:px-6 py-12 sm:py-20">
      {/* Hero */}
      <header className="text-center mb-10">
        <div className="inline-flex items-center gap-2 mb-4 rounded-full border border-white/10 bg-white/[0.04] px-4 py-1.5 text-xs text-slate-400">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          AI-Powered UFC Analytics
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white">
          Fight
          <span className="bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
            Match
          </span>
          <span className="text-slate-500 font-light ml-1.5 text-3xl sm:text-4xl">
            2.0
          </span>
        </h1>
        <p className="mt-3 text-sm sm:text-base text-slate-400 max-w-lg mx-auto leading-relaxed">
          Ask any question about UFC fighters, bouts, and stats.
          <br className="hidden sm:block" />
          Powered by Gemini AI and a live SQLite database.
        </p>
      </header>

      {/* Search */}
      <SearchBar onSubmit={handleQuery} loading={queryLoading} />

      {/* Error */}
      {error && (
        <div className="w-full max-w-2xl mx-auto mt-6 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-300">
          {error}
        </div>
      )}

      {/* Results */}
      {queryLoading && <QuerySkeleton />}
      {!queryLoading && result && <QueryResult result={result} />}

      {/* Divider */}
      <div className="w-full max-w-6xl mx-auto mt-16 mb-0 border-t border-white/[0.05]" />

      {/* Fighter grid */}
      <FighterGrid fighters={fighters} loading={fightersLoading} />

      {/* Footer */}
      <footer className="text-center mt-20 pb-8 text-xs text-slate-600">
        FightMatch 2.0 — Built with FastAPI, SQLAlchemy, Gemini &amp; React
      </footer>
    </div>
  );
}
