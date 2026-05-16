import axios from 'axios'
import type { AgentStepInfo, AnalyzeRequest, AnalyzeResponse, PromptRequest } from '../types'

const api = axios.create({ baseURL: '/api', timeout: 120_000 })

export async function runPromptAnalysis(req: PromptRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>('/prompt', req)
  return data
}

export async function runAnalysis(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>('/analyze', req)
  return data
}

// ---------------------------------------------------------------------------
// Streaming helpers — receive real-time agent events as each agent finishes
// ---------------------------------------------------------------------------

export interface StreamCallbacks {
  onAgentStep: (step: AgentStepInfo) => void
  onComplete: (result: AnalyzeResponse) => void
  onError: (message: string) => void
}

async function _consumeSSE(url: string, body: unknown, callbacks: StreamCallbacks) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!resp.ok || !resp.body) {
    const text = await resp.text()
    callbacks.onError(`Request failed (${resp.status}): ${text}`)
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE messages are separated by double newline
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data: ')) continue
      try {
        const msg = JSON.parse(line.slice(6))
        if (msg.event === 'agent_update') {
          callbacks.onAgentStep(msg.step as AgentStepInfo)
        } else if (msg.event === 'complete') {
          callbacks.onComplete(msg.result as AnalyzeResponse)
        } else if (msg.event === 'error') {
          callbacks.onError(msg.message ?? 'Unknown error')
        }
      } catch {
        // ignore malformed SSE lines
      }
    }
  }
}

export function streamPromptAnalysis(req: PromptRequest, callbacks: StreamCallbacks) {
  return _consumeSSE('/api/prompt/stream', req, callbacks)
}

export function streamAnalysis(req: AnalyzeRequest, callbacks: StreamCallbacks) {
  return _consumeSSE('/api/analyze/stream', req, callbacks)
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
