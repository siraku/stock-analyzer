import { AnalysisRunDetail, AnalysisRunSummary } from '@/types/analysis'
import client from './client'

export const runAnalysis = (tickers?: string[]): Promise<AnalysisRunDetail> =>
  client.post('/analysis/run', { tickers: tickers ?? null }).then((r) => r.data)

export const getLatestAnalysis = (): Promise<AnalysisRunDetail> =>
  client.get('/analysis/latest').then((r) => r.data)

export const listRuns = (limit = 20): Promise<AnalysisRunSummary[]> =>
  client.get('/analysis/runs', { params: { limit } }).then((r) => r.data)

export const getRun = (runId: number): Promise<AnalysisRunDetail> =>
  client.get(`/analysis/runs/${runId}`).then((r) => r.data)
