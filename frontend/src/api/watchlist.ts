import { WatchlistTicker } from '@/types/stock'
import client from './client'

export const getWatchlist = (): Promise<WatchlistTicker[]> =>
  client.get('/watchlist').then((r) => r.data)

export const addTicker = (ticker: string): Promise<WatchlistTicker> =>
  client.post('/watchlist', { ticker }).then((r) => r.data)

export const removeTicker = (ticker: string): Promise<void> =>
  client.delete(`/watchlist/${ticker}`).then(() => undefined)

export const updateTickerNotes = (ticker: string, notes: string): Promise<WatchlistTicker> =>
  client.patch(`/watchlist/${ticker}`, { notes }).then((r) => r.data)
