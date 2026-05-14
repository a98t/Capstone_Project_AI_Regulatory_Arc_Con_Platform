// Shared TypeScript types matching backend Pydantic models

export interface PromptRequest {
  prompt: string
}

export interface AnalyzeRequest {
  building_type: string
  floors: number
  city: string
  material: string
  purpose: string
  notes: string
}

export interface FreshnessInfo {
  verdict: 'CURRENT' | 'AMENDED' | 'UNKNOWN' | 'UNVERIFIED'
  source_url: string
  mcp_verified: boolean
}

export interface FindingItem {
  article_ref: string
  doc_name: string
  status: 'COMPLIANT' | 'VIOLATION' | 'REQUIRES_ACTION' | 'ADVISORY'
  description: string
  plain_language: string
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW' | 'ADVISORY'
  freshness: FreshnessInfo
}

export interface ReportSummary {
  total_norms: number
  violations: number
  requires_action: number
  advisory: number
  compliant: number
  overall_risk: 'HIGH' | 'MEDIUM' | 'LOW' | 'CLEAR' | 'UNKNOWN'
}

export interface AgentStepInfo {
  agent: string
  status: string
  message: string
  duration_ms: number
}

export interface AnalyzeResponse {
  session_id: string
  summary: ReportSummary
  narrative: string
  findings: FindingItem[]
  disclaimer: string
  agent_trace: AgentStepInfo[]
  total_duration_ms: number
  search_confidence: number
  errors: string[]
}

export interface AgentProgressEvent {
  event: 'agent_update' | 'complete' | 'error' | 'connected'
  agent?: string
  status?: string
  message?: string
  duration_ms?: number
  session_id?: string
}
