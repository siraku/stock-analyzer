export type ReversalLikelihood = 'high' | 'medium' | 'low' | 'none'

export interface AnalysisRunSummary {
  id: number
  run_at: string
  status: string
  tickers_analyzed: number | null
  tickers_signaled: number | null
  duration_ms: number | null
}

export interface SignalSnapshot {
  id: number
  ticker: string
  analyzed_at: string
  price_current: number | null
  rsi_14: number | null
  rsi_divergence: boolean | null
  macd_value: number | null
  macd_signal: number | null
  macd_histogram: number | null
  macd_crossover: boolean | null
  ema20: number | null
  ema50: number | null
  bb_upper: number | null
  bb_middle: number | null
  bb_lower: number | null
  bb_bounce: boolean | null
  volume_ratio: number | null
  stoch_k: number | null
  stoch_d: number | null
  stoch_crossover: boolean | null
  candle_pattern: string | null
  pre_score: number | null
  reversal_likelihood: ReversalLikelihood | null
  ai_confidence: number | null
  ai_key_signals: string[] | null
  ai_risk_factors: string[] | null
  ai_summary: string | null
  ai_tokens_used: number | null
}

export interface AnalysisRunDetail {
  run: AnalysisRunSummary
  results: SignalSnapshot[]
}
