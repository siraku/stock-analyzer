import { ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { SignalSnapshot } from '@/types/analysis'
import { formatPrice } from '@/utils/currency'
import IndicatorBar from './IndicatorBar'
import SignalBadge from './SignalBadge'

interface Props {
  snapshot: SignalSnapshot
  companyName?: string | null
  currency?: string | null
}

export default function SignalCard({ snapshot, companyName, currency }: Props) {
  const navigate = useNavigate()
  const isSignificant = snapshot.reversal_likelihood === 'high' || snapshot.reversal_likelihood === 'medium'

  return (
    <div
      className={`bg-gray-900 border rounded-xl p-4 cursor-pointer hover:border-indigo-500/50 transition-colors ${
        snapshot.reversal_likelihood === 'high'
          ? 'border-emerald-500/30'
          : snapshot.reversal_likelihood === 'medium'
          ? 'border-yellow-500/20'
          : 'border-gray-800'
      }`}
      onClick={() => navigate(`/stocks/${snapshot.ticker}`)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <SignalBadge likelihood={snapshot.reversal_likelihood} />
            <span className="font-bold text-white">{snapshot.ticker}</span>
          </div>
          {companyName && (
            <p className="text-xs text-gray-500 mt-0.5">{companyName}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {snapshot.price_current != null && (
            <span className="text-sm text-gray-300 tabular-nums">
              {formatPrice(snapshot.price_current, currency)}
            </span>
          )}
          <ChevronRight size={14} className="text-gray-600" />
        </div>
      </div>

      {/* Indicators */}
      <div className="space-y-1.5 mb-3">
        <IndicatorBar label="RSI(14)" value={snapshot.rsi_14} lowThreshold={30} highThreshold={70} />
        <IndicatorBar label="Stoch %K" value={snapshot.stoch_k} lowThreshold={20} highThreshold={80} />
        {snapshot.volume_ratio != null && (
          <IndicatorBar
            label="Vol ratio"
            value={snapshot.volume_ratio}
            min={0}
            max={4}
            highThreshold={2}
            unit="x"
          />
        )}
      </div>

      {/* Signal tags */}
      {isSignificant && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {snapshot.macd_crossover && <Tag label="MACD Cross" />}
          {snapshot.rsi_divergence && <Tag label="RSI Divergence" />}
          {snapshot.bb_bounce && <Tag label="BB Bounce" />}
          {snapshot.stoch_crossover && <Tag label="Stoch Cross" />}
          {snapshot.candle_pattern && <Tag label={snapshot.candle_pattern} />}
          <Tag label={`Score ${snapshot.pre_score}/150`} muted />
        </div>
      )}

      {/* AI summary */}
      {isSignificant && snapshot.ai_summary && (
        <p className="text-xs text-gray-400 leading-relaxed line-clamp-2">{snapshot.ai_summary}</p>
      )}

      {!isSignificant && (
        <p className="text-xs text-gray-600">No significant reversal signals detected</p>
      )}
    </div>
  )
}

function Tag({ label, muted }: { label: string; muted?: boolean }) {
  return (
    <span
      className={`text-xs px-1.5 py-0.5 rounded ${
        muted ? 'bg-gray-800 text-gray-500' : 'bg-indigo-500/15 text-indigo-400'
      }`}
    >
      {label}
    </span>
  )
}
