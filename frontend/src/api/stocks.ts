import { PriceHistoryResponse, TickerInfo } from '@/types/stock'
import { SignalSnapshot } from '@/types/analysis'
import client from './client'

export const getTickerInfo = (ticker: string): Promise<TickerInfo> =>
  client.get(`/stocks/${ticker}/info`).then((r) => r.data)

export const getPriceHistory = (ticker: string, period = '3mo'): Promise<PriceHistoryResponse> =>
  client.get(`/stocks/${ticker}/price-history`, { params: { period } }).then((r) => r.data)

export const getSignalHistory = (ticker: string, limit = 10): Promise<SignalSnapshot[]> =>
  client.get(`/stocks/${ticker}/signals`, { params: { limit } }).then((r) => r.data)
