import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { getPriceHistory, getTickerInfo } from '@/api/stocks'
import { getSignalHistory } from '@/api/stocks'
import { SignalSnapshot } from '@/types/analysis'
import { PriceBar, TickerInfo } from '@/types/stock'
import { formatPrice } from '@/utils/currency'
import IndicatorBar from '@/components/IndicatorBar'
import SignalBadge from '@/components/SignalBadge'
import PriceChart from '@/components/PriceChart'

export default function StockDetail() {
  const { ticker } = useParams<{ ticker: string }>()
  const navigate = useNavigate()

  const [info, setInfo] = useState<TickerInfo | null>(null)
  const [bars, setBars] = useState<PriceBar[]>([])
  const [signals, setSignals] = useState<SignalSnapshot[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!ticker) return
    setLoading(true)
    Promise.all([
      getTickerInfo(ticker).then(setInfo),
      getPriceHistory(ticker, '3mo').then((r) => setBars(r.bars)),
      getSignalHistory(ticker).then(setSignals),
    ]).finally(() => setLoading(false))
  }, [ticker])

  const latest = signals[0] ?? null

  if (loading) {
    return (
      <div className="p-6 text-center text-gray-600 text-sm">Loading {ticker}...</div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-gray-500 hover:text-white text-sm mb-4 transition-colors"
      >
        <ArrowLeft size={14} />
        Back
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white font-mono">{ticker}</h1>
            {latest && <SignalBadge likelihood={latest.reversal_likelihood} />}
          </div>
          {info?.company_name && (
            <p className="text-gray-400 mt-0.5">{info.company_name}</p>
          )}
          {info?.sector && <p className="text-xs text-gray-600 mt-0.5">{info.sector}</p>}
        </div>
        {info?.current_price && (
          <div className="text-right">
            <p className="text-2xl font-bold text-white tabular-nums">
              {formatPrice(info.current_price, info.currency)}
            </p>
            {info.market_cap && (
              <p className="text-xs text-gray-600 mt-0.5">
                Market cap: {formatPrice(info.market_cap, info.currency)}
              </p>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Chart — spans 2 cols */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-sm font-medium text-gray-400 mb-3">Price Chart (3M)</h2>
          {bars.length > 0 ? (
            <PriceChart bars={bars} snapshot={latest} />
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-700 text-sm">
              No price data available
            </div>
          )}
        </div>

        {/* Indicators panel */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-sm font-medium text-gray-400 mb-4">Indicators</h2>
          {latest ? (
            <div className="space-y-3">
              <IndicatorBar label="RSI(14)" value={latest.rsi_14} lowThreshold={30} highThreshold={70} />
              <IndicatorBar label="Stoch %K" value={latest.stoch_k} lowThreshold={20} highThreshold={80} />
              <IndicatorBar label="Stoch %D" value={latest.stoch_d} lowThreshold={20} highThreshold={80} />
              {latest.volume_ratio != null && (
                <IndicatorBar label="Vol ratio" value={latest.volume_ratio} min={0} max={4} unit="x" />
              )}

              <div className="pt-2 border-t border-gray-800 space-y-1.5 text-xs">
                <Row label="MACD" value={latest.macd_value?.toFixed(2)} />
                <Row label="Signal" value={latest.macd_signal?.toFixed(2)} />
                <Row label="Histogram" value={latest.macd_histogram?.toFixed(2)} />
                <Row label="EMA 20" value={latest.ema20 != null ? formatPrice(latest.ema20, info?.currency) : null} />
                <Row label="EMA 50" value={latest.ema50 != null ? formatPrice(latest.ema50, info?.currency) : null} />
                <Row label="BB Upper" value={latest.bb_upper != null ? formatPrice(latest.bb_upper, info?.currency) : null} />
                <Row label="BB Lower" value={latest.bb_lower != null ? formatPrice(latest.bb_lower, info?.currency) : null} />
                <Row label="Score" value={latest.pre_score != null ? `${latest.pre_score}/150` : null} />
              </div>

              {/* Boolean signals */}
              <div className="pt-2 border-t border-gray-800 flex flex-wrap gap-1.5">
                {latest.macd_crossover && <Tag label="MACD Cross" />}
                {latest.rsi_divergence && <Tag label="RSI Divergence" />}
                {latest.bb_bounce && <Tag label="BB Bounce" />}
                {latest.stoch_crossover && <Tag label="Stoch Cross" />}
                {latest.candle_pattern && <Tag label={latest.candle_pattern} />}
              </div>
            </div>
          ) : (
            <p className="text-gray-600 text-sm">No analysis data yet.</p>
          )}
        </div>
      </div>

      {/* AI Analysis */}
      {latest && latest.reversal_likelihood && latest.reversal_likelihood !== 'none' && (
        <div className="mt-5 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-sm font-medium text-gray-400">AI Analysis</h2>
            <SignalBadge likelihood={latest.reversal_likelihood} />
            {latest.ai_confidence != null && (
              <span className="text-xs text-gray-500">Confidence: {latest.ai_confidence}%</span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {latest.ai_key_signals && latest.ai_key_signals.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">Key Signals</p>
                <ul className="space-y-1">
                  {latest.ai_key_signals.map((s, i) => (
                    <li key={i} className="text-sm text-emerald-400 flex items-start gap-2">
                      <span className="mt-0.5 shrink-0">+</span> {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {latest.ai_risk_factors && latest.ai_risk_factors.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">Risk Factors</p>
                <ul className="space-y-1">
                  {latest.ai_risk_factors.map((r, i) => (
                    <li key={i} className="text-sm text-orange-400 flex items-start gap-2">
                      <span className="mt-0.5 shrink-0">-</span> {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {latest.ai_summary && (
            <p className="mt-4 text-sm text-gray-300 leading-relaxed border-t border-gray-800 pt-4">
              {latest.ai_summary}
            </p>
          )}
        </div>
      )}

      {/* Signal History */}
      {signals.length > 1 && (
        <div className="mt-5 bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-sm font-medium text-gray-400 mb-3">Signal History</h2>
          <div className="flex gap-2 flex-wrap">
            {signals.map((s) => (
              <div
                key={s.id}
                className="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-1.5"
              >
                <span className="text-xs text-gray-500">
                  {new Date(s.analyzed_at).toLocaleDateString('ja-JP')}
                </span>
                <SignalBadge likelihood={s.reversal_likelihood} />
                <span className="text-xs text-gray-600">{s.pre_score}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-600">{label}</span>
      <span className="text-gray-300 tabular-nums">{value ?? '—'}</span>
    </div>
  )
}

function Tag({ label }: { label: string }) {
  return (
    <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-400">{label}</span>
  )
}
