import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { semanticSearch } from '../api/client'

export default function SearchPanel() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])

  const mutation = useMutation({
    mutationFn: () => semanticSearch(query, 10),
    onSuccess: (data) => setResults(data.results ?? []),
  })

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
      <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">
        Document Search
      </h3>
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search regulatory documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && query && mutation.mutate()}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          disabled={!query || mutation.isPending}
          onClick={() => mutation.mutate()}
          className="bg-slate-700 hover:bg-slate-800 disabled:opacity-40 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Search
        </button>
      </div>

      {results.length > 0 && (
        <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
          {results.map((r, i) => (
            <div key={i} className="rounded-lg bg-slate-50 border border-slate-100 px-3 py-2 text-sm">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs text-slate-500">{r.doc_type}</span>
                <span className="font-medium text-slate-700 truncate">{r.doc_name}</span>
                <span className="ml-auto text-xs text-slate-400">{Math.round(r.score * 100)}%</span>
              </div>
              <p className="text-xs text-slate-600 line-clamp-2">{r.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
