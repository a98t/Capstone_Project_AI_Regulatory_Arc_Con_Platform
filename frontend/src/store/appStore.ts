import { create } from 'zustand'
import type { AnalyzeResponse, AgentStepInfo } from '../types'

interface AppState {
  // Analysis result
  result: AnalyzeResponse | null
  isAnalyzing: boolean
  error: string | null

  // Real-time agent progress (SSE)
  agentProgress: AgentStepInfo[]

  // Actions
  setResult: (r: AnalyzeResponse | null) => void
  setIsAnalyzing: (v: boolean) => void
  setError: (e: string | null) => void
  addAgentStep: (step: AgentStepInfo) => void
  resetProgress: () => void
}

export const useAppStore = create<AppState>((set) => ({
  result: null,
  isAnalyzing: false,
  error: null,
  agentProgress: [],

  setResult: (result) => set({ result }),
  setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
  setError: (error) => set({ error }),
  addAgentStep: (step) =>
    set((state) => ({ agentProgress: [...state.agentProgress, step] })),
  resetProgress: () => set({ agentProgress: [], error: null }),
}))
