import { useAppStore } from '../store/appStore'

const AGENT_LABELS: Record<string, string> = {
  SearchAgent: '🔍 Searching regulatory database',
  ComplianceAgent: '⚖️ Analyzing compliance',
  UpdateAgent: '🔄 Verifying norm freshness (MCP)',
  ExplanationAgent: '✍️ Generating report',
}

function formatDuration(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
}

export default function AgentStatusPanel() {
  const { isAnalyzing, agentProgress } = useAppStore()

  if (!isAnalyzing && agentProgress.length === 0) return null

  const completedAgents = new Set(agentProgress.map((s) => s.agent))
  const allAgents = ['SearchAgent', 'ComplianceAgent', 'UpdateAgent', 'ExplanationAgent']
  const allDone = !isAnalyzing && agentProgress.length > 0

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
          Agent Pipeline
        </h3>
        {allDone && (
          <span className="text-xs font-medium text-green-600 bg-green-50 border border-green-200 rounded-full px-2 py-0.5">
            ✓ Complete
          </span>
        )}
      </div>
      <div className="space-y-2">
        {allAgents.map((agent) => {
          const done = completedAgents.has(agent)
          const running = isAnalyzing && !done && allAgents.indexOf(agent) === agentProgress.length
          const step = agentProgress.find((s) => s.agent === agent)

          return (
            <div
              key={agent}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all ${
                done
                  ? 'bg-green-50 border border-green-100 text-green-800'
                  : running
                  ? 'bg-blue-50 border border-blue-100 text-blue-800 animate-pulse'
                  : 'bg-slate-50 border border-transparent text-slate-400'
              }`}
            >
              <span className={`w-5 h-5 flex items-center justify-center rounded-full text-xs font-bold shrink-0 ${
                done
                  ? 'bg-green-500 text-white'
                  : running
                  ? 'bg-blue-500 text-white'
                  : 'bg-slate-200 text-slate-400'
              }`}>
                {done ? '✓' : running ? '…' : '○'}
              </span>
              <span className="flex-1 font-medium">{AGENT_LABELS[agent] ?? agent}</span>
              {step ? (
                <span className={`text-xs font-mono tabular-nums ${
                  done ? 'text-green-600' : 'text-slate-400'
                }`}>
                  {formatDuration(step.duration_ms)}
                </span>
              ) : running ? (
                <span className="text-xs text-blue-400">running…</span>
              ) : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}
