export interface WatchlistTicker {
  id: number
  ticker: string
  company_name: string | null
  sector: string | null
  market_cap: number | null
  currency: string | null
  added_at: string
  is_active: boolean
  notes: string | null
}

export interface PriceBar {
  date: string
  open: number | null
  high: number | null
  low: number | null
  close: number | null
  volume: number | null
}

export interface PriceHistoryResponse {
  ticker: string
  bars: PriceBar[]
}

export interface TickerInfo {
  ticker: string
  company_name: string | null
  current_price: number | null
  sector: string | null
  market_cap: number | null
  currency: string | null
}
