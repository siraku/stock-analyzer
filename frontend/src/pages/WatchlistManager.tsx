import { useEffect, useState } from 'react'
import { Plus, Trash2, Loader2 } from 'lucide-react'
import { addTicker, getWatchlist, removeTicker, updateTickerNotes } from '@/api/watchlist'
import { WatchlistTicker } from '@/types/stock'

export default function WatchlistManager() {
  const [tickers, setTickers] = useState<WatchlistTicker[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getWatchlist()
      .then(setTickers)
      .finally(() => setLoading(false))
  }, [])

  const handleAdd = async () => {
    const ticker = input.trim().toUpperCase()
    if (!ticker) return
    setAdding(true)
    setError(null)
    try {
      const newTicker = await addTicker(ticker)
      setTickers((prev) => [...prev, newTicker])
      setInput('')
    } catch (e: unknown) {
      const axiosErr = e as { response?: { data?: { detail?: string } } }
      setError(axiosErr?.response?.data?.detail ?? 'Failed to add ticker')
    } finally {
      setAdding(false)
    }
  }

  const handleRemove = async (ticker: string) => {
    try {
      await removeTicker(ticker)
      setTickers((prev) => prev.filter((t) => t.ticker !== ticker))
    } catch {
      // ignore
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleAdd()
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-white mb-6">Watchlist</h1>

      {/* Add form */}
      <div className="flex gap-2 mb-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. AAPL, TSLA, 7203.T"
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 font-mono"
        />
        <button
          onClick={handleAdd}
          disabled={adding || !input.trim()}
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
        >
          {adding ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
          Add
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-400 mb-4">{error}</p>
      )}

      {/* Table */}
      {loading ? (
        <div className="text-center py-12 text-gray-600 text-sm">Loading...</div>
      ) : tickers.length === 0 ? (
        <div className="text-center py-12 text-gray-600 text-sm">
          No tickers yet. Add a TSE stock code above (e.g. 7203.T)
        </div>
      ) : (
        <div className="space-y-2">
          {tickers.map((t) => (
            <div
              key={t.ticker}
              className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-xl px-4 py-3"
            >
              <div className="flex items-center gap-4">
                <span className="font-mono font-bold text-white">{t.ticker}</span>
                <div>
                  <p className="text-sm text-gray-300">{t.company_name ?? '—'}</p>
                  {t.sector && <p className="text-xs text-gray-600">{t.sector}</p>}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-600">
                  {new Date(t.added_at).toLocaleDateString('ja-JP')}
                </span>
                <button
                  onClick={() => handleRemove(t.ticker)}
                  className="p-1.5 text-gray-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="mt-6 text-xs text-gray-600">
        Supports US stocks (<code className="font-mono text-gray-500">AAPL</code>),
        Japan (<code className="font-mono text-gray-500">7203.T</code>),
        HK (<code className="font-mono text-gray-500">0700.HK</code>), and other Yahoo Finance tickers.
      </p>
    </div>
  )
}
