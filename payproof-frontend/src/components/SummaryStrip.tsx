import type { Case } from '../types'

interface Props {
  cases: Case[]
}

/**
 * Summary strip — 3 stat cards at the top of the dashboard.
 * Numbers in IBM Plex Mono, labels in Inter/Slate.
 */
export default function SummaryStrip({ cases }: Props) {
  const total = cases.length

  const scoresWithValue = cases.filter((c) => c.completeness_score !== null)
  const avgCompleteness =
    scoresWithValue.length > 0
      ? Math.round(
          scoresWithValue.reduce((sum, c) => sum + (c.completeness_score ?? 0), 0) /
            scoresWithValue.length
        )
      : null

  const pendingReview = cases.filter((c) => c.status === 'human_review').length

  const stats = [
    { label: 'Total Cases', value: total.toString() },
    {
      label: 'Avg Completeness',
      value: avgCompleteness !== null ? `${avgCompleteness}%` : '—',
    },
    {
      label: 'Requiring Human Review',
      value: pendingReview.toString(),
      highlight: pendingReview > 0,
    },
  ]

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 12,
        marginBottom: 28,
      }}
    >
      {stats.map((s) => (
        <div
          key={s.label}
          className="card"
          style={{ padding: '18px 22px' }}
        >
          <div
            className="font-mono"
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: s.highlight ? 'var(--color-amber)' : 'var(--color-white)',
              lineHeight: 1.1,
              marginBottom: 6,
            }}
          >
            {s.value}
          </div>
          <div
            className="font-body text-slate"
            style={{ fontSize: 13 }}
          >
            {s.label}
          </div>
        </div>
      ))}
    </div>
  )
}
