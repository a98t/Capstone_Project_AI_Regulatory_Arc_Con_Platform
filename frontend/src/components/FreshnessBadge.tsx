import type { FreshnessInfo } from '../types'

const VERDICT_CONFIG = {
  CURRENT: { label: 'Current', className: 'bg-green-100 text-green-800' },
  AMENDED: { label: 'Amended', className: 'bg-amber-100 text-amber-800' },
  UNKNOWN: { label: 'Unknown', className: 'bg-slate-100 text-slate-600' },
  UNVERIFIED: { label: 'Unverified', className: 'bg-slate-100 text-slate-500' },
}

export default function FreshnessBadge({ freshness }: { freshness: FreshnessInfo }) {
  const config = VERDICT_CONFIG[freshness.verdict] ?? VERDICT_CONFIG.UNKNOWN

  return (
    <a
      href={freshness.source_url || undefined}
      target="_blank"
      rel="noopener noreferrer"
      title={freshness.mcp_verified ? 'Verified via MCP/Tavily' : 'Not MCP-verified'}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.className} ${
        freshness.source_url ? 'hover:opacity-80 cursor-pointer' : 'cursor-default'
      }`}
    >
      {freshness.mcp_verified ? '🔗' : '○'} {config.label}
    </a>
  )
}
