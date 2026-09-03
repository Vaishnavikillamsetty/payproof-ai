import type { Evidence } from '../types'

interface Props {
  /** 0???100 */
  score: number | null
  /** Show a text label beside the bar */
  showLabel?: boolean
  /** Show the detailed available/missing checklist below the bar */
  showChecklist?: boolean
  /** List of evidence records for the case */
  evidence?: Evidence[]
}

const CRITICAL_EVIDENCE = [
  { id: 'payment', label: 'Payment record' },
  { id: 'delivery', label: 'Delivery confirmation' },
  { id: 'otp', label: 'OTP / Verification' },
  { id: 'communication', label: 'Merchant communication' }
]

/**
 * Progress bar showing evidence completeness score, plus an itemized checklist.
 */
export default function CompletenessBar({ score, showLabel = true, showChecklist = false, evidence = [] }: Props) {
  if (score === null) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div
          style={{
            flex: 1,
            height: 4,
            borderRadius: 2,
            background: 'var(--color-ink-border)',
          }}
        />
        {showLabel && (
          <span
            className="font-mono text-slate"
            style={{ fontSize: 12, minWidth: 32, textAlign: 'right' }}
          >
            ???
          </span>
        )}
      </div>
    )
  }

  const pct = Math.max(0, Math.min(100, score))
  const color =
    pct >= 70
      ? 'var(--color-teal)'
      : pct >= 40
        ? 'var(--color-amber)'
        : 'var(--color-red)'

  // Determine what is missing and what is present
  const presentTypes = new Set(evidence.map(e => e.evidence_type))
  const available = CRITICAL_EVIDENCE.filter(c => presentTypes.has(c.id))
  const missing = CRITICAL_EVIDENCE.filter(c => !presentTypes.has(c.id))

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <div
          style={{
            flex: 1,
            height: 4,
            borderRadius: 2,
            background: 'var(--color-ink-border)',
            overflow: 'hidden',
          }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Evidence completeness ${pct}%`}
        >
          <div
            style={{
              width: `${pct}%`,
              height: '100%',
              background: color,
              borderRadius: 2,
              transition: 'width 0.4s ease',
            }}
          />
        </div>
        {showLabel && (
          <span
            className="font-mono"
            style={{ fontSize: 12, color, minWidth: 32, textAlign: 'right' }}
          >
            {available.length} / 4 categories available
          </span>
        )}
      </div>
      
      {showChecklist && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          <div>
            <h4 className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', marginBottom: 8 }}>Available</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, gap: 4, display: 'flex', flexDirection: 'column' }}>
              {available.map(item => (
                <li key={item.id} className="font-body text-slate" style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: 'var(--color-teal)' }}>???</span> {item.label}
                </li>
              ))}
              {available.length === 0 && <li className="font-body text-slate-light" style={{ fontSize: 13, fontStyle: 'italic' }}>None</li>}
            </ul>
          </div>
          <div>
            <h4 className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', marginBottom: 8 }}>Missing</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, gap: 4, display: 'flex', flexDirection: 'column' }}>
              {missing.map(item => (
                <li key={item.id} className="font-body text-slate" style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: 'var(--color-red)' }}>???</span> {item.label}
                </li>
              ))}
              {missing.length === 0 && <li className="font-body text-slate-light" style={{ fontSize: 13, fontStyle: 'italic' }}>None</li>}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
