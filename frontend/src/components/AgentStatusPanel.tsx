import { useAppStore } from '../store/appStore'

const AGENT_LABELS: Record<string, string> = {
  SearchAgent: '🔍 Searching regulatory database',
  ComplianceAgent: '⚖️ Analyzing compliance',
  UpdateAgent: '🔄 Verifying norm freshness (MCP)',
  ExplanationAgent: '✍️ Generating report',
}

export default function AgentStatusPanel() {
  const { isAnalyzing, agentProgress } = useAppStore()

  if (!isAnalyzing && agentProgress.length === 0) return null

  const completedAgents = new Set(agentProgress.map((s) => s.agent))
  const allAgents = ['SearchAgent', 'ComplianceAgent', 'UpdateAgent', 'ExplanationAgent']

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
      <h3 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wide">
        Agent Pipeline
      </h3>
      <div className="space-y-2">
        {allAgents.map((agent) => {
          const done = completedAgents.has(agent)
          const running = isAnalyzing && !done && allAgents.indexOf(agent) === agentProgress.length
          const step = agentProgress.find((s) => s.agent === agent)

          return (
            <div
              key={agent}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                done ? 'bg-green-50 text-green-800' :
                running ? 'bg-blue-50 text-blue-800 animate-pulse' :
                'bg-slate-50 text-slate-400'
              }`}
            >
              <span className="w-4 text-center">
                {done ? '✓' : running ? '⟳' : '○'}
              </span>
              <span className="flex-1">{AGENT_LABELS[agent] ?? agent}</span>
              {step && (
                <span className="text-xs opacity-60">{step.duration_ms}ms</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
