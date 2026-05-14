import type { FindingItem } from '../types'
import FreshnessBadge from './FreshnessBadge'

const STATUS_STYLES: Record<string, string> = {
  VIOLATION: 'border-red-400 bg-red-50',
  REQUIRES_ACTION: 'border-amber-400 bg-amber-50',
  ADVISORY: 'border-blue-300 bg-blue-50',
  COMPLIANT: 'border-green-400 bg-green-50',
}

const STATUS_BADGE: Record<string, string> = {
  VIOLATION: 'bg-red-100 text-red-800',
  REQUIRES_ACTION: 'bg-amber-100 text-amber-800',
  ADVISORY: 'bg-blue-100 text-blue-800',
  COMPLIANT: 'bg-green-100 text-green-800',
}

export default function FindingCard({ finding }: { finding: FindingItem }) {
  const borderClass = STATUS_STYLES[finding.status] ?? 'border-slate-300 bg-white'
  const badgeClass = STATUS_BADGE[finding.status] ?? 'bg-slate-100 text-slate-600'

  return (
    <div className={`rounded-xl border-l-4 p-4 ${borderClass}`}>
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${badgeClass}`}>
            {finding.status.replace('_', ' ')}
          </span>
          <span className="text-xs font-mono text-slate-500">{finding.article_ref}</span>
          <FreshnessBadge freshness={finding.freshness} />
        </div>
        <span className="text-xs text-slate-400">{finding.doc_name}</span>
      </div>

      <p className="mt-2 text-sm text-slate-700">{finding.description}</p>

      {finding.plain_language && finding.plain_language !== finding.description && (
        <p className="mt-1 text-sm text-slate-500 italic">{finding.plain_language}</p>
      )}
    </div>
  )
}
