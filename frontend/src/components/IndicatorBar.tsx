interface Props {
  label: string
  value: number | null
  min?: number
  max?: number
  lowThreshold?: number
  highThreshold?: number
  unit?: string
}

export default function IndicatorBar({
  label,
  value,
  min = 0,
  max = 100,
  lowThreshold,
  highThreshold,
  unit = '',
}: Props) {
  const pct = value != null ? Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100) : 0

  const barColor =
    lowThreshold != null && value != null && value < lowThreshold
      ? 'bg-emerald-500'
      : highThreshold != null && value != null && value > highThreshold
      ? 'bg-red-500'
      : 'bg-indigo-500'

  return (
    <div className="flex items-center gap-3">
      <span className="w-16 text-xs text-gray-400 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-16 text-right text-xs text-gray-300 shrink-0 tabular-nums">
        {value != null ? `${value}${unit}` : '—'}
      </span>
    </div>
  )
}
