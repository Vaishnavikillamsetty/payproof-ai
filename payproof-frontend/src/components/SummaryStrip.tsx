import type { Case } from '../types'
import { formatAmount } from '../utils'

interface Props {
  cases: Case[]
}

const OPEN_LIFECYCLES = new Set([
  'NEW', 'OPEN', 'INVESTIGATING', 'PENDING_REVIEW', 'HUMAN_REVIEW', 'ESCALATE', 'ESCALATED',
  'REQUEST_MORE_EVIDENCE', 'EVIDENCE_REQUESTED', 'STRONG_CASE', 'WEAK_CASE', 'CONTEST',
  'ACCEPT', 'ACTION_REQUIRED', 'UNDER_REVIEW', 'DECISION_RECORDED',
  'new', 'open', 'investigating', 'pending_review', 'human_review', 'escalate', 'escalated',
  'request_more_evidence', 'evidence_requested', 'strong_case', 'weak_case', 'contest',
  'accept', 'action_required', 'under_review', 'decision_recorded',
])

export default function SummaryStrip({ cases }: Props) {
  const openCases = cases.filter(c => OPEN_LIFECYCLES.has(c.status) && c.status.toLowerCase() !== 'resolved' && c.status.toLowerCase() !== 'closed')
  const amountAtRiskByCurrency = new Map<string, number>()
  for (const c of openCases) {
    const currency = c.currency?.trim().toUpperCase() || 'UNKNOWN'
    amountAtRiskByCurrency.set(currency, (amountAtRiskByCurrency.get(currency) ?? 0) + (c.amount ?? 0))
  }
  const amountAtRisk = [...amountAtRiskByCurrency.entries()]
    .map(([currency, amount]) => formatAmount(amount, currency))
    .join(' · ')

  const recommendationsReady = cases.filter(c =>
    c.ai_recommendation !== null &&
    !c.human_decision &&
    !['resolved', 'closed', 'RESOLVED', 'CLOSED'].includes(c.status)
  ).length

  const pendingReview = cases.filter(c =>
    !c.human_decision &&
    !['resolved', 'closed', 'RESOLVED', 'CLOSED'].includes(c.status)
  ).length

  const stats = [
    {
      label: 'Open Cases',
      value: openCases.length.toString(),
      sub: `${cases.length} total`,
      color: 'var(--color-white)',
    },
    {
      label: 'Amount at Risk',
      value: openCases.length > 0 ? amountAtRisk : '—',
      sub: 'open cases only',
      color: openCases.length > 0 ? 'var(--color-amber)' : 'var(--color-white)',
    },
    {
      label: 'AI Recommendations Ready',
      value: recommendationsReady.toString(),
      sub: 'advisory analysis complete',
      color: recommendationsReady > 0 ? 'var(--color-teal)' : 'var(--color-white)',
    },
    {
      label: 'Pending Human Decision',
      value: pendingReview.toString(),
      sub: 'awaiting review or action',
      color: pendingReview > 0 ? 'var(--color-red)' : 'var(--color-white)',
    },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-7">
      {stats.map((s) => (
        <div key={s.label} className="card" style={{ padding: '18px 22px' }}>
          <div
            className="font-mono"
            style={{
              fontSize: s.value.length > 6 ? 18 : 26,
              fontWeight: 700,
              color: s.color,
              lineHeight: 1.1,
              marginBottom: 4,
            }}
          >
            {s.value}
          </div>
          <div className="font-body" style={{ fontSize: 13, color: 'var(--color-white)', marginBottom: 3 }}>
            {s.label}
          </div>
          <div className="font-mono text-slate" style={{ fontSize: 10, letterSpacing: '0.04em' }}>
            {s.sub}
          </div>
        </div>
      ))}
    </div>
  )
}
