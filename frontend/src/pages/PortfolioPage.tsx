import { useState } from 'react'
import { ChevronDown, ChevronRight, FolderOpen, TrendingUp, TrendingDown, Pencil, Check, X } from 'lucide-react'
import { analyzePortfolio, renameGroup, reassignTicker } from '@/api/portfolio'
import { PortfolioAnalysis, ThemeGroup, PortfolioPosition } from '@/types/portfolio'

const DEFAULT_PATH = 'C:\\Users\\le.shi\\Desktop\\stock'

export default function PortfolioPage() {
  const [filePath, setFilePath] = useState(DEFAULT_PATH)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<PortfolioAnalysis | null>(null)

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await analyzePortfolio(filePath)
      setData(result)
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (e instanceof Error ? e.message : 'Analysis failed')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleRename = async (oldName: string, newName: string) => {
    if (oldName === newName || !newName.trim()) return
    await renameGroup(oldName, newName.trim())
    setData(prev => {
      if (!prev) return prev
      const trimmed = newName.trim()
      return {
        ...prev,
        groups: prev.groups.map(g =>
          g.group_name === oldName
            ? {
                ...g,
                group_name: trimmed,
                positions: g.positions.map(p => ({ ...p, group_name: trimmed })),
              }
            : g
        ),
      }
    })
  }

  const handleReassign = async (ticker: string, newGroupName: string) => {
    const trimmed = newGroupName.trim()
    if (!trimmed) return
    await reassignTicker(ticker, trimmed)
    setData(prev => {
      if (!prev) return prev

      let movedPos: PortfolioPosition | undefined

      // Remove from current group
      const updatedGroups = prev.groups
        .map(g => {
          const pos = g.positions.find(p => p.ticker === ticker)
          if (pos) {
            movedPos = { ...pos, group_name: trimmed }
            return { ...g, positions: g.positions.filter(p => p.ticker !== ticker) }
          }
          return g
        })
        .filter(g => g.positions.length > 0)

      if (!movedPos) return prev

      // Add to target group (or create it)
      const targetIdx = updatedGroups.findIndex(g => g.group_name === trimmed)
      if (targetIdx >= 0) {
        updatedGroups[targetIdx] = {
          ...updatedGroups[targetIdx],
          positions: [...updatedGroups[targetIdx].positions, movedPos],
        }
      } else {
        updatedGroups.push({
          group_name: trimmed,
          positions: [movedPos],
          total_value_jpy: 0,
          total_pnl_jpy: 0,
          pnl_pct: 0,
          value_pct: 0,
          position_count: 0,
        })
      }

      // Recalculate stats for all groups
      const totalValue = prev.total_value_jpy
      const recalculated = updatedGroups.map(g => {
        const value = g.positions.reduce((s, p) => s + p.current_value_jpy, 0)
        const pnl = g.positions.reduce((s, p) => s + p.pnl_jpy, 0)
        const cost = value - pnl
        return {
          ...g,
          total_value_jpy: value,
          total_pnl_jpy: pnl,
          pnl_pct: cost > 0 ? parseFloat(((pnl / cost) * 100).toFixed(2)) : 0,
          value_pct: totalValue > 0 ? parseFloat(((value / totalValue) * 100).toFixed(1)) : 0,
          position_count: g.positions.length,
        }
      })
      recalculated.sort((a, b) => b.total_value_jpy - a.total_value_jpy)

      return { ...prev, groups: recalculated }
    })
  }

  const allGroupNames = data?.groups.map(g => g.group_name) ?? []

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">Portfolio Breakdown</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Thematic groups — AI-classified on first run, editable anytime
        </p>
      </div>

      {/* File path input */}
      <div className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <FolderOpen size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            placeholder="Path to CSV file or folder containing it"
            className="w-full pl-9 pr-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading || !filePath.trim()}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors"
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {loading && (
        <div className="mb-4 px-4 py-3 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-400">
          Classifying positions via AI — new tickers may take ~10 seconds...
        </div>
      )}

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Summary strip */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            <StatCard label="Total Value" value={`¥${Math.round(data.total_value_jpy).toLocaleString()}`} />
            <StatCard
              label="Unrealized P&L"
              value={`${data.total_pnl_jpy >= 0 ? '+' : ''}¥${Math.round(data.total_pnl_jpy).toLocaleString()}`}
              sub={`${data.pnl_pct >= 0 ? '+' : ''}${data.pnl_pct.toFixed(2)}%`}
              positive={data.total_pnl_jpy >= 0}
            />
            <StatCard
              label="Positions"
              value={String(data.position_count)}
              sub={`${data.groups.length} groups`}
            />
          </div>

          {/* Group cards */}
          <div className="space-y-3">
            {data.groups.map(group => (
              <GroupCard
                key={group.group_name}
                group={group}
                totalValue={data.total_value_jpy}
                allGroupNames={allGroupNames}
                onRename={handleRename}
                onReassign={handleReassign}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  positive,
}: {
  label: string
  value: string
  sub?: string
  positive?: boolean
}) {
  const subColor =
    positive === undefined ? 'text-gray-500' : positive ? 'text-emerald-400' : 'text-red-400'
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-lg font-bold text-white">{value}</p>
      {sub && <p className={`text-xs mt-0.5 ${subColor}`}>{sub}</p>}
    </div>
  )
}

function GroupCard({
  group,
  totalValue,
  allGroupNames,
  onRename,
  onReassign,
}: {
  group: ThemeGroup
  totalValue: number
  allGroupNames: string[]
  onRename: (oldName: string, newName: string) => Promise<void>
  onReassign: (ticker: string, groupName: string) => Promise<void>
}) {
  const [expanded, setExpanded] = useState(true)
  const [editing, setEditing] = useState(false)
  const [nameValue, setNameValue] = useState(group.group_name)

  const isPositive = group.total_pnl_jpy >= 0
  const barPct = totalValue > 0 ? (group.total_value_jpy / totalValue) * 100 : 0

  const startEditing = (e: React.MouseEvent) => {
    e.stopPropagation()
    setNameValue(group.group_name)
    setEditing(true)
  }

  const commitEdit = async (e?: React.MouseEvent) => {
    e?.stopPropagation()
    setEditing(false)
    await onRename(group.group_name, nameValue)
  }

  const cancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditing(false)
    setNameValue(group.group_name)
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {/* Group header */}
      <div
        onClick={() => !editing && setExpanded(v => !v)}
        className="group w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-800/50 transition-colors cursor-pointer"
      >
        {expanded
          ? <ChevronDown size={14} className="text-gray-500 shrink-0" />
          : <ChevronRight size={14} className="text-gray-500 shrink-0" />}

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-4">
            {/* Group name — inline editable */}
            <div className="flex items-center gap-1.5 min-w-0" onClick={e => e.stopPropagation()}>
              {editing ? (
                <>
                  <input
                    autoFocus
                    onFocus={e => e.target.select()}
                    value={nameValue}
                    onChange={e => setNameValue(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') commitEdit()
                      if (e.key === 'Escape') { setEditing(false); setNameValue(group.group_name) }
                    }}
                    className="text-sm font-semibold bg-gray-800 border border-indigo-500 rounded px-2 py-0.5 text-white focus:outline-none w-48"
                  />
                  <button
                    onClick={commitEdit}
                    className="text-emerald-400 hover:text-emerald-300 p-0.5"
                  >
                    <Check size={12} />
                  </button>
                  <button onClick={cancelEdit} className="text-gray-500 hover:text-gray-400 p-0.5">
                    <X size={12} />
                  </button>
                </>
              ) : (
                <>
                  <span className="text-sm font-semibold text-white truncate">{group.group_name}</span>
                  <button
                    onClick={startEditing}
                    className="text-gray-600 hover:text-gray-400 opacity-0 group-hover:opacity-100 p-0.5 transition-opacity"
                  >
                    <Pencil size={11} />
                  </button>
                </>
              )}
            </div>

            <div className="flex items-center gap-4 shrink-0">
              <span className="text-xs text-gray-500">{group.position_count} stocks</span>
              <span className="text-sm font-medium text-white">
                ¥{Math.round(group.total_value_jpy).toLocaleString()}
              </span>
              <span className={`text-xs font-medium flex items-center gap-0.5 ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                {isPositive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                {isPositive ? '+' : ''}{group.pnl_pct.toFixed(1)}%
              </span>
              <span className="text-xs text-gray-500 w-10 text-right">
                {group.value_pct.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Value proportion bar */}
          <div className="mt-2 h-1 bg-gray-800 rounded-full">
            <div
              className={`h-1 rounded-full ${isPositive ? 'bg-indigo-500' : 'bg-red-500/70'}`}
              style={{ width: `${barPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Positions table */}
      {expanded && (
        <div className="border-t border-gray-800">
          <div className="grid grid-cols-[1fr_auto_auto_auto_auto_1.5rem] gap-x-4 px-5 py-1.5 text-[10px] text-gray-600 uppercase tracking-wide border-b border-gray-800/40 bg-gray-950/50">
            <span>Stock</span>
            <span className="text-right">Qty</span>
            <span className="text-right">Avg Cost</span>
            <span className="text-right">Value (JPY)</span>
            <span className="text-right">P&amp;L</span>
            <span />
          </div>
          {group.positions.map(pos => (
            <PositionRow
              key={pos.ticker}
              pos={pos}
              allGroupNames={allGroupNames}
              onReassign={onReassign}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function PositionRow({
  pos,
  allGroupNames,
  onReassign,
}: {
  pos: PortfolioPosition
  allGroupNames: string[]
  onReassign: (ticker: string, groupName: string) => Promise<void>
}) {
  const [reassigning, setReassigning] = useState(false)
  const [groupInput, setGroupInput] = useState('')
  const isPositive = pos.pnl_jpy >= 0
  const listId = `groups-${pos.ticker}`

  const commitReassign = async () => {
    const trimmed = groupInput.trim()
    setReassigning(false)
    if (!trimmed || trimmed === pos.group_name) return
    await onReassign(pos.ticker, trimmed)
  }

  return (
    <div className="grid grid-cols-[1fr_auto_auto_auto_auto_1.5rem] gap-x-4 px-5 py-2 text-xs border-b border-gray-800/20 last:border-b-0 hover:bg-gray-800/20 items-center">
      <div className="min-w-0">
        <span className="font-medium text-white">{pos.ticker}</span>
        <span className="text-gray-500 ml-2 truncate">{pos.company_name}</span>
      </div>
      <span className="text-gray-400 text-right">{pos.quantity}</span>
      <span className="text-gray-400 text-right">${pos.avg_cost.toFixed(2)}</span>
      <span className="text-gray-300 text-right">
        ¥{Math.round(pos.current_value_jpy).toLocaleString()}
      </span>
      <span className={`text-right font-medium ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
        {isPositive ? '+' : ''}{pos.pnl_pct.toFixed(1)}%
      </span>

      {/* Reassign control */}
      <div className="relative flex items-center justify-end">
        {reassigning ? (
          <div className="flex items-center gap-1 absolute right-6 z-10 bg-gray-900 border border-gray-700 rounded-lg px-2 py-1.5 shadow-lg">
            <datalist id={listId}>
              {allGroupNames.map(g => <option key={g} value={g} />)}
            </datalist>
            <input
              list={listId}
              autoFocus
              value={groupInput}
              onChange={e => setGroupInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') commitReassign()
                if (e.key === 'Escape') setReassigning(false)
              }}
              onBlur={commitReassign}
              placeholder="Group name…"
              className="w-36 bg-transparent text-xs text-white placeholder-gray-600 focus:outline-none"
            />
            <button onClick={commitReassign} className="text-emerald-400 hover:text-emerald-300 shrink-0">
              <Check size={11} />
            </button>
            <button onClick={() => setReassigning(false)} className="text-gray-500 hover:text-gray-400 shrink-0">
              <X size={11} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => { setGroupInput(''); setReassigning(true) }}
            title="Move to different group"
            className="text-gray-700 hover:text-indigo-400 transition-colors"
          >
            <Pencil size={11} />
          </button>
        )}
      </div>
    </div>
  )
}
