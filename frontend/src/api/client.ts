import axios from 'axios'
import type { AnalyzeRequest, AnalyzeResponse, PromptRequest } from '../types'

const api = axios.create({ baseURL: '/api', timeout: 120_000 })

export async function runPromptAnalysis(req: PromptRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>('/prompt', req)
  return data
}

export async function runAnalysis(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>('/analyze', req)
  return data
}

export async function semanticSearch(query: string, limit = 20) {
  const { data } = await api.post('/search', { query, limit })
  return data
}

export async function submitFeedback(
  session_id: string,
  rating: number,
  comment: string
) {
  const { data } = await api.post('/feedback', { session_id, rating, comment })
  return data
}
