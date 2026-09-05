import { motion, useReducedMotion } from 'framer-motion'
import type { Case } from '../types'
import { formatAmount, formatDate, formatDisputeReason, shortTxn, statusTheme, aiRecommendationLabel, isDemoCase, lifecycleStatus } from '../utils'
import CompletenessBar from './CompletenessBar'

interface Props {
  case_: Case
  index: number
  onSelect: (id: string) => void
}

const REC_COLORS: Record<string, string> = {
  CONTEST: 'var(--color-teal)',
  ACCEPT: 'var(--color-teal)',
  'REQUEST MORE EVIDENCE': 'var(--color-amber)',
  'HUMAN REVIEW': 'var(--color-red)',
  ESCALATE: 'var(--color-red)',
  INVESTIGATING: 'var(--color-slate)',
  PENDING: 'var(--color-slate)',
}

export default function CaseCard({ case_: c, index, onSelect }: Props) {
  const shouldReduceMotion = useReducedMotion()
  const lifecycle = lifecycleStatus(c.status, c.ai_recommendation, c.final_action)
  const theme = statusTheme(lifecycle)
  const rec = c.ai_recommendation ? aiRecommendationLabel(c.ai_recommendation) : '-'
  const recColor = c.ai_recommendation ? (REC_COLORS[rec] ?? 'var(--color-slate)') : 'var(--color-slate)'
  const isDemo = isDemoCase(c.transaction_id)

  const confidence =
    c.overall_confidence !== null && c.overall_confidence !== undefined
      ? `${Math.round(c.overall_confidence * 100)}%`
      : '--'

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 10 }}
      animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: shouldReduceMotion ? 0 : index * 0.06, ease: 'easeOut' }}
      style={{ cursor: 'pointer' }}
      onClick={() => onSelect(c.id)}
      role="button"
      tabIndex={0}
      id={`case-card-${c.id}`}
      aria-label={`Case ${c.transaction_id} - ${formatDisputeReason(c.dispute_reason)}, AI recommendation: ${rec}`}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect(c.id) }}
    >
      <div
        className={`card ${theme.edgeClass} grid grid-cols-1 md:grid-cols-[1fr_180px_160px_160px_32px] gap-4 items-start md:items-center`}
        style={{ padding: '14px 18px', marginBottom: 8, transition: 'border-color 0.15s ease, background 0.15s ease' }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.background = '#172032'
          ;(e.currentTarget as HTMLElement).style.borderColor = '#2A3A50'
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.background = 'var(--color-ink-light)'
          ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--color-ink-border)'
        }}
      >
        {/* ---- Col 1: Identity ---- */}
        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
            <div
              className="font-mono"
              style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-white)', letterSpacing: '0.05em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
            >
              {shortTxn(c.transaction_id)}
            </div>
            {isDemo && (
              <span
                className="font-mono"
                style={{ fontSize: 9, padding: '1px 6px', background: 'rgba(91,107,124,0.25)', border: '1px solid var(--color-ink-border)', borderRadius: 3, color: 'var(--color-slate)', letterSpacing: '0.06em', whiteSpace: 'nowrap' }}
              >
                DEMO
              </span>
            )}
          </div>
          <div
            className="font-body"
            style={{ fontSize: 13, color: 'var(--color-white)', opacity: 0.85, marginBottom: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
          >
            {formatDisputeReason(c.dispute_reason)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="font-mono text-slate" style={{ fontSize: 11 }}>{c.merchant_id.toUpperCase()}</span>
            <span className="font-mono" style={{ fontSize: 12, color: 'var(--color-slate-light)', fontWeight: 600 }}>{formatAmount(c.amount, c.currency)}</span>
          </div>
        </div>

        {/* ---- Col 2: Completeness ---- */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
            <span className="font-body text-slate" style={{ fontSize: 10 }}>Evidence Strength</span>
            <span className="font-mono text-slate" style={{ fontSize: 10 }}>{confidence}</span>
          </div>
          <CompletenessBar
            score={c.completeness_score}
            showLabel={true}
            evidence={(c.evidence_types ?? []).map((t, i) => ({
              id: `${c.id}-ev-${i}`,
              case_id: c.id,
              evidence_type: t,
              source_id: null,
              content: {},
              event_timestamp: null,
              collected_at: c.created_at,
            }))}
          />
        </div>

        {/* ---- Col 3: Lifecycle status ---- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-start' }}>
          <span className="font-mono text-slate" style={{ fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>Lifecycle</span>
          <span
            className="font-mono"
            style={{ fontSize: 11, padding: '2px 8px', background: `color-mix(in srgb, ${theme.dot} 15%, transparent)`, color: theme.dot, borderRadius: 3, textTransform: 'uppercase', letterSpacing: '0.04em' }}
          >
            {theme.label}
          </span>
          <span className="font-mono text-slate" style={{ fontSize: 10 }}>{formatDate(c.created_at)}</span>
        </div>

        {/* ---- Col 4: AI Recommendation ---- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-start' }}>
          <span className="font-mono text-slate" style={{ fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>AI Recommendation</span>
          <span
            className="font-mono"
            style={{ fontSize: 11, padding: '2px 8px', background: `color-mix(in srgb, ${recColor} 15%, transparent)`, color: recColor, borderRadius: 3, textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}
          >
            {rec}
          </span>
        </div>

        {/* ---- Col 5: Chevron ---- */}
        <div className="flex justify-end md:justify-center w-full mt-2 md:mt-0">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M6 4l4 4-4 4" stroke="var(--color-slate)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </motion.div>
  )
}
