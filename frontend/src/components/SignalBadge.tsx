import { ReversalLikelihood } from '@/types/analysis'

const config: Record<
  ReversalLikelihood,
  { label: string; classes: string }
> = {
  high: { label: 'HIGH', classes: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' },
  medium: { label: 'MED', classes: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' },
  low: { label: 'LOW', classes: 'bg-orange-500/20 text-orange-400 border border-orange-500/30' },
  none: { label: 'NONE', classes: 'bg-gray-700/40 text-gray-500 border border-gray-700' },
}

interface Props {
  likelihood: ReversalLikelihood | null
}

export default function SignalBadge({ likelihood }: Props) {
  const key = likelihood ?? 'none'
  const { label, classes } = config[key]
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold tracking-widest ${classes}`}>
      {label}
    </span>
  )
}
