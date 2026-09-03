import type { Case } from '../types'
import { formatAmount } from '../utils'

interface Props {
  cases: Case[]
}

const ACTIVE_STATUSES = ['new', 'investigating', 'strong_case', 'weak_case', 'human_review',
  'request_more_evidence', 'escalate', 'contest', 'accept', 'action_required', 'under_review']

export default function SummaryStrip({ cases }: Props) {
  const active = cases.filter(c => ACTIVE_STATUSES.includes(c.status))
  const amountAtRisk = active.reduce((sum, c) => sum + (c.amount ?? 0), 0)

  const recommendationsReady = cases.filter(c =>
    ['strong_case', 'weak_case', 'request_more_evidence', 'escalate', 'contest', 'accept']
      .includes(c.status) && c.overall_confidence !== null
  ).length

  const pendingReview = cases.filter(c =>
    c.status === 'human_review' || c.status === 'escalate'
  ).length

  const stats = [
    {
      label: 'Active Disputes',
      value: active.length.toString(),
      sub: `${cases.length} total`,
      color: 'var(--color-white)',
    },
    {
      label: 'Amount at Risk',
      value: active.length > 0 ? formatAmount(amountAtRisk) : '???',
      sub: 'open cases only',
      color: amountAtRisk > 0 ? 'var(--color-amber)' : 'var(--color-white)',
    },
    {
      label: 'AI Recommendations Ready',
      value: recommendationsReady.toString(),
      sub: 'awaiting human decision',
      color: recommendationsReady > 0 ? 'var(--color-teal)' : 'var(--color-white)',
    },
    {
      label: 'Require Human Review',
      value: pendingReview.toString(),
      sub: 'escalated or flagged',
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
