import { motion } from 'framer-motion'
import type { Evidence } from '../types'
import { formatDate, evidenceProvenance } from '../utils'

interface Props {
  evidenceList: Evidence[]
}

const PROVENANCE_CONFIG = {
  razorpay: {
    label: 'VERIFIED BY RAZORPAY',
    icon: '???',
    color: 'var(--color-teal)',
    bg: 'rgba(63,167,150,0.08)',
    border: 'rgba(63,167,150,0.25)',
    dotColor: '#3FA796',
  },
  merchant: {
    label: 'MERCHANT EVIDENCE',
    icon: '???',
    color: 'var(--color-amber)',
    bg: 'rgba(224,163,57,0.08)',
    border: 'rgba(224,163,57,0.25)',
    dotColor: '#E0A339',
  },
  ai: {
    label: 'AI ANALYSIS',
    icon: '????',
    color: 'var(--color-slate-light)',
    bg: 'rgba(91,107,124,0.08)',
    border: 'rgba(91,107,124,0.25)',
    dotColor: '#5B6B7C',
  },
}

function isDemo(e: Evidence): boolean {
  const note = e.content?.note as string | undefined
  return typeof note === 'string' && note.startsWith('[DEMO]')
}

function evidenceTypeLabel(evType: string): string {
  return evType.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function renderEvidenceFields(content: Record<string, unknown>) {
  const skip = new Set(['note'])
  const entries = Object.entries(content).filter(([k]) => !skip.has(k))
  if (entries.length === 0) return null
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 24px', marginTop: 8 }}>
      {entries.map(([key, val]) => (
        <div key={key} style={{ minWidth: 120 }}>
          <span className="font-mono" style={{ fontSize: 10, color: 'rgba(0,0,0,0.45)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block' }}>{key.replace(/_/g, ' ')}</span>
          <span className="font-mono" style={{ fontSize: 12, color: 'rgba(0,0,0,0.75)', fontWeight: 500 }}>
            {typeof val === 'boolean' ? (val ? 'Yes' : 'No') : String(val ?? '???')}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function EvidencePanel({ evidenceList }: Props) {
  const hasDemo = evidenceList.some(isDemo)

  // Group by provenance
  const groups: Record<'razorpay' | 'merchant' | 'ai', Evidence[]> = { razorpay: [], merchant: [], ai: [] }
  for (const e of evidenceList) {
    groups[evidenceProvenance(e.evidence_type)].push(e)
  }

  const orderedTiers: ('razorpay' | 'merchant' | 'ai')[] = ['razorpay', 'merchant', 'ai']

  return (
    <div>
      {hasDemo && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'rgba(91,107,124,0.12)', border: '1px solid var(--color-ink-border)',
          borderRadius: 4, padding: '8px 12px', marginBottom: 20,
        }}>
          <span style={{ fontSize: 13 }}>??????</span>
          <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.04em' }}>
            DEMO DATA ??? evidence retrieved from seeded demo records simulating payment gateway, courier, OTP, and communication systems.
          </span>
        </div>
      )}

      {evidenceList.length === 0 && (
        <div style={{ padding: '24px 0', textAlign: 'center' }}>
          <div className="font-mono text-slate" style={{ fontSize: 13 }}>??? MISSING INFORMATION</div>
          <div className="font-body text-slate" style={{ fontSize: 14, marginTop: 8, fontStyle: 'italic' }}>
            No evidence was collected for this case. Investigation may require manual evidence submission.
          </div>
        </div>
      )}

      {orderedTiers.map(tier => {
        const items = groups[tier]
        if (items.length === 0) return null
        const cfg = PROVENANCE_CONFIG[tier]
        return (
          <div key={tier} style={{ marginBottom: 24 }}>
            {/* Tier header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <span style={{ fontSize: 13 }}>{cfg.icon}</span>
              <span
                className="font-mono"
                style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', color: cfg.color, textTransform: 'uppercase' }}
              >
                {cfg.label}
              </span>
              <div style={{ flex: 1, height: 1, background: cfg.border }} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {items.map((e, i) => (
                <motion.div
                  key={e.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06, duration: 0.25, ease: 'easeOut' }}
                  style={{
                    background: cfg.bg,
                    border: `1px solid ${cfg.border}`,
                    borderRadius: 6,
                    padding: '14px 18px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                    <div>
                      <span
                        className="font-mono"
                        style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink)', textTransform: 'uppercase', letterSpacing: '0.05em' }}
                      >
                        {evidenceTypeLabel(e.evidence_type)}
                      </span>
                      <div style={{ display: 'flex', gap: 8, marginTop: 3 }}>
                        {isDemo(e) && (
                          <span
                            className="font-mono"
                            style={{ fontSize: 9, padding: '1px 5px', background: 'rgba(0,0,0,0.08)', borderRadius: 2, color: 'rgba(0,0,0,0.4)', letterSpacing: '0.06em' }}
                          >
                            DEMO
                          </span>
                        )}
                        {e.source_id && (
                          <span className="font-mono" style={{ fontSize: 9, color: 'rgba(0,0,0,0.4)' }}>
                            {e.source_id}
                          </span>
                        )}
                      </div>
                    </div>
                    {e.event_timestamp && (
                      <span className="font-mono" style={{ fontSize: 10, color: 'rgba(0,0,0,0.4)', whiteSpace: 'nowrap' }}>
                        {formatDate(e.event_timestamp)}
                      </span>
                    )}
                  </div>
                  {renderEvidenceFields(e.content as Record<string, unknown>)}
                </motion.div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
