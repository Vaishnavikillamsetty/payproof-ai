import { motion, useReducedMotion } from 'framer-motion'
import type { Case } from '../types'
import { formatAmount, formatDate, formatDisputeReason, shortTxn, statusTheme } from '../utils'
import CompletenessBar from './CompletenessBar'
import VerdictStamp from './VerdictStamp'

interface Props {
  case_: Case
  index: number
  onSelect: (id: string) => void
}

/**
 * Index-card style row for the case list.
 *
 * Layout: [left-edge accent] [transaction/dispute info] [completeness bar] [status badge + date] [chevron]
 *
 * Animates in staggered on mount (80ms per card, per build-plan §8).
 * Respects prefers-reduced-motion.
 */
export default function CaseCard({ case_: c, index, onSelect }: Props) {
  const shouldReduceMotion = useReducedMotion()
  const theme = statusTheme(c.status)

  const confidence =
    c.overall_confidence !== null && c.overall_confidence !== undefined
      ? `${Math.round(c.overall_confidence * 100)}%`
      : '—'

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 10 }}
      animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
      transition={{
        duration: 0.25,
        delay: shouldReduceMotion ? 0 : index * 0.06, // ~60ms stagger per card
        ease: 'easeOut',
      }}
      style={{ cursor: 'pointer' }}
      onClick={() => onSelect(c.id)}
      role="button"
      tabIndex={0}
      id={`case-card-${c.id}`}
      aria-label={`Case ${c.transaction_id} — ${formatDisputeReason(c.dispute_reason)}, status: ${theme.label}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onSelect(c.id)
      }}
    >
      <div
        className={`card ${theme.edgeClass} grid grid-cols-1 md:grid-cols-[1fr_200px_200px_32px] gap-5 items-start md:items-center`}
        style={{
          padding: '16px 20px',
          marginBottom: 8,
          transition: 'border-color 0.15s ease, background 0.15s ease',
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.background = '#172032'
          ;(e.currentTarget as HTMLElement).style.borderColor = '#2A3A50'
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.background = 'var(--color-ink-light)'
          ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--color-ink-border)'
        }}
      >
        {/* ── Col 1: Identity ────────────────────────────────────────── */}
        <div style={{ minWidth: 0 }}>
          <div
            className="font-mono"
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--color-white)',
              letterSpacing: '0.05em',
              marginBottom: 4,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {shortTxn(c.transaction_id)}
          </div>
          <div
            className="font-body"
            style={{
              fontSize: 14,
              color: 'var(--color-white)',
              opacity: 0.85,
              marginBottom: 4,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {formatDisputeReason(c.dispute_reason)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span
              className="font-mono text-slate"
              style={{ fontSize: 11, letterSpacing: '0.04em' }}
            >
              {c.merchant_id.toUpperCase()}
            </span>
            <span
              className="font-mono"
              style={{ fontSize: 11, color: 'var(--color-slate-light)' }}
            >
              {formatAmount(c.amount)}
            </span>
          </div>
        </div>

        {/* ── Col 2: Completeness + Confidence ───────────────────────── */}
        <div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: 6,
            }}
          >
            <span className="font-body text-slate" style={{ fontSize: 11 }}>
              Completeness
            </span>
            <span className="font-body text-slate" style={{ fontSize: 11 }}>
              Confidence
            </span>
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
          <div
            style={{
              marginTop: 6,
              display: 'flex',
              justifyContent: 'flex-end',
            }}
          >
            <span
              className="font-mono"
              style={{ fontSize: 12, color: 'var(--color-slate-light)' }}
            >
              {confidence}
            </span>
          </div>
        </div>

        {/* ── Col 3: Status badge + timestamp ────────────────────────── */}
        <div className="flex flex-row md:flex-col items-center md:items-end justify-between w-full md:w-auto mt-2 md:mt-0">
          <div className="md:mb-3">
            <VerdictStamp status={c.status} confidence={c.overall_confidence} size="small" />
          </div>
          <div
            className="font-mono text-slate"
            style={{ fontSize: 11, letterSpacing: '0.03em' }}
          >
            {formatDate(c.created_at)}
          </div>
        </div>

        {/* ── Col 4: Chevron ─────────────────────────────────────────── */}
        <div className="flex justify-end md:justify-center w-full mt-2 md:mt-0">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M6 4l4 4-4 4"
              stroke="var(--color-slate)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>
    </motion.div>
  )
}
