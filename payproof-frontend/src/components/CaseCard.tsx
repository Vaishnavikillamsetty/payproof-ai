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
  APPROVE: 'var(--color-teal)',
  CONTEST: 'var(--color-teal)',
  ACCEPT: 'var(--color-teal)',
  'REQUEST MORE EVIDENCE': 'var(--color-amber)',
  'HUMAN REVIEW': 'var(--color-red)',
  ESCALATE: 'var(--color-red)',
  INVESTIGATING: 'var(--color-slate)',
  PENDING: 'var(--color-slate)',
}

const STRENGTH_COLORS: Record<string, string> = {
  HIGH: 'var(--color-teal)',
  MEDIUM: 'var(--color-amber)',
  LOW: 'var(--color-red)',
  NOT_EVALUATED: 'var(--color-slate)',
}

const STRENGTH_BG: Record<string, string> = {
  HIGH: 'rgba(54, 198, 174, 0.12)',
  MEDIUM: 'rgba(240, 168, 48, 0.12)',
  LOW: 'rgba(224, 82, 82, 0.12)',
  NOT_EVALUATED: 'rgba(100, 116, 139, 0.10)',
}

export default function CaseCard({ case_: c, index, onSelect }: Props) {
  const shouldReduceMotion = useReducedMotion()
  const lifecycle = lifecycleStatus(c.status, c.ai_recommendation, c.human_decision ?? c.final_action)
  const theme = statusTheme(lifecycle)
  const rec = c.ai_recommendation ? aiRecommendationLabel(c.ai_recommendation) : '-'
  const recColor = c.ai_recommendation ? (REC_COLORS[rec] ?? 'var(--color-slate)') : 'var(--color-slate)'
  const isDemo = isDemoCase(c.transaction_id)
  const strength = (c.evidence_strength || 'NOT_EVALUATED').toUpperCase()
  const strengthColor = STRENGTH_COLORS[strength] || 'var(--color-slate)'
  const strengthBg = STRENGTH_BG[strength] || 'rgba(100, 116, 139, 0.10)'

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
      animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
      transition={{ duration: 0.22, delay: shouldReduceMotion ? 0 : index * 0.05, ease: 'easeOut' }}
      style={{ cursor: 'pointer' }}
      onClick={() => onSelect(c.id)}
      role="button"
      tabIndex={0}
      id={`case-card-${c.id}`}
      aria-label={`Case ${c.transaction_id} - ${formatDisputeReason(c.dispute_reason)}, AI recommendation: ${rec}`}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect(c.id) }}
    >
      <div
        className={`card ${theme.edgeClass} grid grid-cols-1 md:grid-cols-[1fr_190px_155px_155px_28px] gap-4 items-start md:items-center`}
        style={{
          padding: '16px 20px',
          marginBottom: 8,
          transition: 'border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease',
        }}
        onMouseEnter={(e) => {
          const el = e.currentTarget as HTMLElement
          el.style.background = 'var(--color-ink-mid)'
          el.style.borderColor = '#2A3D55'
          el.style.boxShadow = '0 4px 16px rgba(0,0,0,0.35)'
          el.style.transform = 'translateY(-1px)'
        }}
        onMouseLeave={(e) => {
          const el = e.currentTarget as HTMLElement
          el.style.background = 'var(--color-ink-light)'
          el.style.borderColor = 'var(--color-ink-border)'
          el.style.boxShadow = '0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)'
          el.style.transform = 'translateY(0)'
        }}
      >
        {/* ---- Col 1: Identity ---- */}
        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <div
              className="font-mono"
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: 'var(--color-white)',
                letterSpacing: '0.06em',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {shortTxn(c.transaction_id)}
            </div>
            {isDemo && (
              <span
                className="font-mono"
                style={{
                  fontSize: 9,
                  padding: '2px 6px',
                  background: 'rgba(100, 116, 139, 0.15)',
                  border: '1px solid var(--color-ink-border)',
                  borderRadius: 4,
                  color: 'var(--color-slate)',
                  letterSpacing: '0.08em',
                  whiteSpace: 'nowrap',
                }}
              >
                DEMO
              </span>
            )}
          </div>
          <div
            className="font-body"
            style={{
              fontSize: 13,
              fontWeight: 500,
              color: 'var(--color-white)',
              opacity: 0.88,
              marginBottom: 5,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {formatDisputeReason(c.dispute_reason)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="font-mono" style={{ fontSize: 11, color: 'var(--color-slate)', letterSpacing: '0.03em' }}>
              {c.merchant_id.toUpperCase()}
            </span>
            <span
              className="font-mono"
              style={{ fontSize: 12, color: 'var(--color-slate-light)', fontWeight: 600 }}
            >
              {formatAmount(c.amount, c.currency)}
            </span>
          </div>
        </div>

        {/* ---- Col 2: Evidence Categories & Strength ---- */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span className="font-mono" style={{ fontSize: 10, color: 'var(--color-slate)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              Evidence
            </span>
            <span
              className="font-mono"
              style={{
                fontSize: 10,
                fontWeight: 700,
                color: strengthColor,
                background: strengthBg,
                padding: '1px 7px',
                borderRadius: 4,
                letterSpacing: '0.04em',
              }}
            >
              {strength}
            </span>
          </div>
          <CompletenessBar
            score={c.completeness_score}
            showLabel={true}
            categoriesAvailable={c.categories_available}
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, alignItems: 'flex-start' }}>
          <span className="font-mono" style={{ fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--color-slate)' }}>
            Lifecycle
          </span>
          <span
            className="font-mono"
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: '3px 9px',
              background: `color-mix(in srgb, ${theme.dot} 14%, transparent)`,
              color: theme.dot,
              borderRadius: 5,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              border: `1px solid color-mix(in srgb, ${theme.dot} 30%, transparent)`,
            }}
          >
            {theme.label}
          </span>
          <span className="font-mono" style={{ fontSize: 10, color: 'var(--color-slate)' }}>
            {formatDate(c.created_at)}
          </span>
        </div>

        {/* ---- Col 4: AI Recommendation & Human Decision ---- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, alignItems: 'flex-start' }}>
          <span className="font-mono" style={{ fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--color-slate)' }}>
            AI Rec.
          </span>
          <span
            className="font-mono"
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: '3px 9px',
              background: `color-mix(in srgb, ${recColor} 12%, transparent)`,
              color: recColor,
              borderRadius: 5,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              whiteSpace: 'nowrap',
              border: `1px solid color-mix(in srgb, ${recColor} 25%, transparent)`,
            }}
          >
            {rec}
          </span>
          {c.human_decision && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 2, paddingTop: 4, borderTop: '1px solid var(--color-ink-border)', width: '100%' }}>
              <span className="font-mono" style={{ fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-slate)' }}>
                Human Dec.
              </span>
              <span
                className="font-mono"
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  color: 'var(--color-white)',
                  letterSpacing: '0.03em',
                }}
              >
                {c.human_decision.toUpperCase()}
              </span>
            </div>
          )}
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
