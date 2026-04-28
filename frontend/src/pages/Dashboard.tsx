import { useEffect, useState } from 'react'
import { Play, RefreshCw, Clock } from 'lucide-react'
import { runAnalysis, getLatestAnalysis } from '@/api/analysis'
import { getWatchlist } from '@/api/watchlist'
import { useAnalysisStore } from '@/store/analysisStore'
import { SignalSnapshot, ReversalLikelihood } from '@/types/analysis'
import { WatchlistTicker } from '@/types/stock'
import SignalCard from '@/components/SignalCard'

type FilterMode = 'all' | 'high' | 'medium' | 'low' | 'none'

export default function Dashboard() {
  const { latest, isRunning, error, setLatest, setRunning, setError } = useAnalysisStore()
  const [watchlist, setWatchlist] = useState<WatchlistTicker[]>([])
  const [filter, setFilter] = useState<FilterMode>('all')

  // Load watchlist for company names
  useEffect(() => {
    getWatchlist().then(setWatchlist).catch(() => {})
  }, [])

  // Load last run on mount
  useEffect(() => {
    getLatestAnalysis().then(setLatest).catch(() => {})
  }, [])

  const companyMap = Object.fromEntries(
    watchlist.map((t) => [t.ticker, t.company_name])
  )
  const currencyMap = Object.fromEntries(
    watchlist.map((t) => [t.ticker, t.currency])
  )

  const handleRun = async () => {
    setRunning(true)
    setError(null)
    try {
      const result = await runAnalysis()
      setLatest(result)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Analysis failed'
      setError(msg)
    } finally {
      setRunning(false)
    }
  }

  const filtered: SignalSnapshot[] = (latest?.results ?? []).filter((s) => {
    if (filter === 'all') return true
    return s.reversal_likelihood === filter
  })

  const counts = {
    high: latest?.results.filter((s) => s.reversal_likelihood === 'high').length ?? 0,
    medium: latest?.results.filter((s) => s.reversal_likelihood === 'medium').length ?? 0,
    low: latest?.results.filter((s) => s.reversal_likelihood === 'low').length ?? 0,
    none: latest?.results.filter((s) => s.reversal_likelihood === 'none').length ?? 0,
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">Reversal Analysis</h1>
          {latest && (
            <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
              <Clock size={11} />
              Last run: {new Date(latest.run.run_at).toLocaleString('ja-JP')}
              {latest.run.duration_ms && ` · ${(latest.run.duration_ms / 1000).toFixed(1)}s`}
            </p>
          )}
        </div>
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors"
        >
          {isRunning ? (
            <RefreshCw size={14} className="animate-spin" />
          ) : (
            <Play size={14} />
          )}
          {isRunning ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Filter tabs */}
      {latest && (
        <div className="flex items-center gap-2 mb-5 flex-wrap">
          <FilterTab label="All" count={latest.results.length} active={filter === 'all'} onClick={() => setFilter('all')} />
          <FilterTab label="High" count={counts.high} active={filter === 'high'} color="emerald" onClick={() => setFilter('high')} />
          <FilterTab label="Medium" count={counts.medium} active={filter === 'medium'} color="yellow" onClick={() => setFilter('medium')} />
          <FilterTab label="Low" count={counts.low} active={filter === 'low'} color="orange" onClick={() => setFilter('low')} />
          <FilterTab label="None" count={counts.none} active={filter === 'none'} color="gray" onClick={() => setFilter('none')} />
        </div>
      )}

      {/* Empty state */}
      {!latest && !isRunning && (
        <div className="text-center py-24 text-gray-600">
          <BarChartIcon />
          <p className="mt-3 text-sm">No analysis yet.</p>
          <p className="text-xs mt-1">Add tickers to your watchlist and click Run Analysis.</p>
        </div>
      )}

      {/* Loading skeleton */}
      {isRunning && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4 animate-pulse h-28" />
          ))}
        </div>
      )}

      {/* Results */}
      {!isRunning && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map((s) => (
            <SignalCard key={s.id} snapshot={s} companyName={companyMap[s.ticker]} currency={currencyMap[s.ticker]} />
          ))}
        </div>
      )}

      {!isRunning && latest && filtered.length === 0 && (
        <p className="text-center text-gray-600 py-12 text-sm">No stocks match this filter.</p>
      )}
    </div>
  )
}

function FilterTab({
  label,
  count,
  active,
  color = 'indigo',
  onClick,
}: {
  label: string
  count: number
  active: boolean
  color?: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
        active
          ? 'bg-indigo-600 text-white'
          : 'bg-gray-800 text-gray-400 hover:text-white'
      }`}
    >
      {label}
      <span className={`px-1.5 py-0.5 rounded text-xs ${active ? 'bg-white/20' : 'bg-gray-700'}`}>
        {count}
      </span>
    </button>
  )
}

function BarChartIcon() {
  return (
    <svg className="mx-auto w-12 h-12 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  )
}
