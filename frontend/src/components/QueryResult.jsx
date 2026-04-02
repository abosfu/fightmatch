export default function QueryResult({ result }) {
  if (!result) return null;

  const { sql, data, explanation } = result;

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 flex flex-col gap-6 animate-in">
      {/* Explanation card */}
      {explanation && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6 shadow-2xl">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/15">
              <svg className="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-blue-400 tracking-wide uppercase">
              AI Analysis
            </h3>
          </div>
          <p className="text-[15px] leading-relaxed text-slate-200">{explanation}</p>
        </div>
      )}

      {/* SQL card */}
      {sql && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl p-5 shadow-lg">
          <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
            Generated SQL
          </h4>
          <pre className="overflow-x-auto text-[13px] leading-relaxed text-emerald-400/80 font-mono whitespace-pre-wrap break-words">
            {sql}
          </pre>
        </div>
      )}

      {/* Data table */}
      {data && data.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl shadow-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-white/[0.06]">
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Results — {data.length} row{data.length !== 1 ? "s" : ""}
            </h4>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  {Object.keys(data[0]).map((col) => (
                    <th
                      key={col}
                      className="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap"
                    >
                      {col.replace(/_/g, " ")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"
                  >
                    {Object.values(row).map((val, j) => (
                      <td
                        key={j}
                        className="px-5 py-3 text-slate-300 whitespace-nowrap"
                      >
                        {val ?? "—"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data && data.length === 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl p-6 text-center text-slate-500">
          No results returned for this query.
        </div>
      )}
    </div>
  );
}
