import { create } from 'zustand'
import { AnalysisRunDetail } from '@/types/analysis'

interface AnalysisState {
  latest: AnalysisRunDetail | null
  isRunning: boolean
  error: string | null
  setLatest: (data: AnalysisRunDetail | null) => void
  setRunning: (v: boolean) => void
  setError: (msg: string | null) => void
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  latest: null,
  isRunning: false,
  error: null,
  setLatest: (data) => set({ latest: data ?? null }),
  setRunning: (v) => set({ isRunning: v }),
  setError: (msg) => set({ error: msg }),
}))
