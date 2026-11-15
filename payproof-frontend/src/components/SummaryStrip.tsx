import type { Case } from '../types'
import { formatAmount } from '../utils'

interface Props {
  cases: Case[]
}

const OPEN_LIFECYCLES = new Set([
  'new', 'open', 'investigating', 'pending_review', 'human_review', 'escalate', 'escalated',
  'request_more_evidence', 'evidence_requested', 'strong_case', 'weak_case', 'contest',
  'accept', 'action_required', 'under_review', 'decision_recorded',
])

const INVALID_AI_RECS = new Set([
  '', 'none', 'unknown', 'failed', 'error', 'ai_analysis_unavailable', 'null', 'undefined'
])

const WAITING_FOR_EVIDENCE_STATUSES = new Set([
  'request_more_evidence',
  'evidence_requested',
])

const TERMINAL_STATUSES = new Set([
  'resolved',
  'closed',
  'won',
  'lost',
])

/**
 * Checks whether an AI recommendation was successfully generated and is valid.
 * Independent of whether a human reviewed it or whether the case was resolved.
 */
export function isValidAiRecommendation(rec: string | null | undefined): boolean {
  if (!rec) return false
  const trimmed = rec.trim().toLowerCase()
  return !INVALID_AI_RECS.has(trimmed)
}

/**
 * Checks if a case is genuinely awaiting a human reviewer decision.
 * Criteria:
 * - Valid AI recommendation exists (AI analysis complete)
 * - No human decision recorded yet
 * - Not waiting for additional evidence (evidence_requested / request_more_evidence)
 * - Not resolved or closed
 */
export function isPendingHumanDecision(c: Case): boolean {
  // 1. Must have a valid AI recommendation
  if (!isValidAiRecommendation(c.ai_recommendation)) {
    return false
  }

  // 2. EXCLUDE: Cases where a human decision has already been recorded
  if (c.human_decision && c.human_decision.trim() !== '') {
    return false
  }

  const normalizedStatus = (c.status || '').trim().toLowerCase()

  // 3. EXCLUDE: Cases waiting for additional evidence
  if (WAITING_FOR_EVIDENCE_STATUSES.has(normalizedStatus)) {
    return false
  }

  // 4. EXCLUDE: Cases that are resolved or closed
  if (TERMINAL_STATUSES.has(normalizedStatus)) {
    return false
  }

  // 5. Active case awaiting human review
  return true
}

export default function SummaryStrip({ cases }: Props) {
  const openCases = cases.filter(c => {
    const s = (c.status || '').trim().toLowerCase()
    return OPEN_LIFECYCLES.has(s) && !TERMINAL_STATUSES.has(s)
  })

  const amountAtRiskByCurrency = new Map<string, number>()
  for (const c of openCases) {
    const currency = c.currency?.trim().toUpperCase() || 'UNKNOWN'
    amountAtRiskByCurrency.set(currency, (amountAtRiskByCurrency.get(currency) ?? 0) + (c.amount ?? 0))
  }
  const amountAtRisk = [...amountAtRiskByCurrency.entries()]
    .map(([currency, amount]) => formatAmount(amount, currency))
    .join(' · ')

  // Count ALL cases with valid AI recommendations regardless of human decision or status
  const recommendationsReady = cases.filter(c => isValidAiRecommendation(c.ai_recommendation)).length

  // Count cases genuinely awaiting a human reviewer decision
  const pendingReview = cases.filter(isPendingHumanDecision).length

  const stats = [
    {
      label: 'Open Cases',
      value: openCases.length.toString(),
      sub: `${cases.length} total cases`,
      color: 'var(--color-white)',
    },
    {
      label: 'Amount at Risk',
      value: openCases.length > 0 ? amountAtRisk : '—',
      sub: 'Open cases only',
      color: openCases.length > 0 ? 'var(--color-amber)' : 'var(--color-white)',
    },
    {
      label: 'AI Recommendations Ready',
      value: recommendationsReady.toString(),
      sub: 'Cases with successfully completed AI recommendations, including previously reviewed cases.',
      color: recommendationsReady > 0 ? 'var(--color-teal)' : 'var(--color-white)',
    },
    {
      label: 'Pending Human Decision',
      value: pendingReview.toString(),
      sub: "Cases currently awaiting a human reviewer's decision.",
      color: pendingReview > 0 ? 'var(--color-red)' : 'var(--color-white)',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-7">
      {stats.map((s) => (
        <div
          key={s.label}
          className="card"
          style={{
            padding: '18px 20px',
            background: 'linear-gradient(180deg, #131A27 0%, #0F1622 100%)',
            border: '1px solid var(--color-ink-border)',
            borderRadius: 8,
            boxShadow: '0 2px 6px rgba(0, 0, 0, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            minHeight: 135,
          }}
        >
          <div>
            <div
              className="font-mono"
              style={{
                fontSize: s.value.length > 10 ? 19 : s.value.length > 6 ? 23 : 28,
                fontWeight: 700,
                color: s.color,
                lineHeight: 1.15,
                marginBottom: 6,
                letterSpacing: '-0.02em',
              }}
            >
              {s.value}
            </div>
            <div
              className="font-body"
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--color-white)',
                letterSpacing: '0.01em',
                marginBottom: 8,
              }}
            >
              {s.label}
            </div>
          </div>
          <div
            style={{
              fontSize: 11,
              lineHeight: 1.45,
              color: 'var(--color-slate-light)',
            }}
          >
            {s.sub}
          </div>
        </div>
      ))}
    </div>
  )
}

