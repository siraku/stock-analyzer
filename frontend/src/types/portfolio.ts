export interface PortfolioPosition {
  ticker: string
  company_name: string
  account: string
  quantity: number
  avg_cost: number
  cost_currency: string
  current_price: number
  current_value_jpy: number
  pnl_jpy: number
  pnl_pct: number
  group_name: string
}

export interface ThemeGroup {
  group_name: string
  positions: PortfolioPosition[]
  total_value_jpy: number
  total_pnl_jpy: number
  pnl_pct: number
  value_pct: number
  position_count: number
}

export interface PortfolioAnalysis {
  groups: ThemeGroup[]
  total_value_jpy: number
  total_pnl_jpy: number
  pnl_pct: number
  position_count: number
}
