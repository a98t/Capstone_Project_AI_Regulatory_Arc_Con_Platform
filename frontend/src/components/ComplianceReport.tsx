import type { AnalyzeResponse } from '../types'
import FindingCard from './FindingCard'

const RISK_STYLES: Record<string, string> = {
  HIGH: 'bg-red-600',
  MEDIUM: 'bg-amber-500',
  LOW: 'bg-yellow-400',
  CLEAR: 'bg-green-500',
  UNKNOWN: 'bg-slate-400',
}

export default function ComplianceReport({ report }: { report: AnalyzeResponse }) {
  const { summary, narrative, findings, disclaimer, total_duration_ms, search_confidence } = report
  const riskColor = RISK_STYLES[summary.overall_risk] ?? RISK_STYLES.UNKNOWN

  return (
    <div className="space-y-5">
      {/* Summary bar */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
        <div className="flex items-center gap-3 mb-4">
          <span className={`rounded-full px-3 py-1 text-white text-sm font-bold ${riskColor}`}>
            {summary.overall_risk} RISK
          </span>
          <span className="text-xs text-slate-400">
            {total_duration_ms}ms · confidence {Math.round(search_confidence * 100)}%
          </span>
        </div>

        <div className="grid grid-cols-4 gap-3 text-center">
          {[
            { label: 'Violations', value: summary.violations, color: 'text-red-600' },
            { label: 'Requires Action', value: summary.requires_action, color: 'text-amber-600' },
            { label: 'Advisory', value: summary.advisory, color: 'text-blue-600' },
            { label: 'Compliant', value: summary.compliant, color: 'text-green-600' },
          ].map(({ label, value, color }) => (
            <div key={label}>
              <div className={`text-2xl font-bold ${color}`}>{value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>

        {/* Plain-language narrative */}
        {narrative && (
          <div className="mt-4 rounded-xl bg-slate-50 border border-slate-100 p-4 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
            {narrative}
          </div>
        )}
      </div>

      {/* Findings */}
      {findings.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-2">
            Findings ({findings.length})
          </h3>
          <div className="space-y-3">
            {findings.map((f, i) => (
              <FindingCard key={i} finding={f} />
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-xs text-amber-800">
        {disclaimer}
      </div>
    </div>
  )
}
