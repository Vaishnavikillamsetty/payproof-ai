import { motion, useReducedMotion } from 'framer-motion'
import type { Evidence } from '../types'
import { formatDate } from '../utils'

interface Props {
  evidenceList: Evidence[]
}

/**
 * Vertical evidence timeline.
 * Animates in staggered on load. Cards use paper color.
 */
function isDemo(e: Evidence): boolean {
  const note = e.content?.note as string | undefined
  return typeof note === 'string' && note.startsWith('[DEMO]')
}

export default function EvidenceTimeline({ evidenceList }: Props) {
  const shouldReduceMotion = useReducedMotion()
  const hasDemo = evidenceList.some(isDemo)

  return (
    <div>
      {hasDemo && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'rgba(91, 107, 124, 0.15)',
          border: '1px solid var(--color-ink-border)',
          borderRadius: 4, padding: '8px 12px', marginBottom: 20,
        }}>
          <span style={{ fontSize: 14 }}>⚗️</span>
          <span className="font-body text-slate" style={{ fontSize: 12, lineHeight: 1.4 }}>
            <strong>Evidence retrieved from seeded demo records simulating payment gateway, courier, OTP, and merchant communication systems.</strong>
          </span>
        </div>
      )}
      <div style={{ position: 'relative', paddingLeft: 24 }}>
      {/* Vertical line */}
      <div
        style={{
          position: 'absolute',
          left: 7,
          top: 10,
          bottom: 0,
          width: 2,
          background: 'var(--color-ink-border)',
        }}
      />

      {evidenceList.map((e, index) => {
        const hasTimestamp = e.event_timestamp != null
        
        return (
          <motion.div
            key={e.id}
            initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: shouldReduceMotion ? 0 : index * 0.08, ease: 'easeOut', duration: 0.3 }}
            style={{ position: 'relative', marginBottom: 24 }}
          >
            {/* Timeline dot */}
            <div
              style={{
                position: 'absolute',
                left: -21, // 24 - 3
                top: 14,
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: 'var(--color-slate-light)',
                border: '2px solid var(--color-ink)',
                zIndex: 2,
              }}
            />
            {/* The pinned card */}
            <div
              style={{
                background: 'var(--color-paper)',
                color: 'var(--color-ink)',
                padding: '16px 20px',
                borderRadius: 4,
                boxShadow: 'var(--shadow)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8, borderBottom: '1px solid rgba(0,0,0,0.1)', paddingBottom: 8 }}>
                <div>
                  <span className="font-mono" style={{ fontWeight: 600, fontSize: 13, textTransform: 'uppercase' }}>
                    📄 {e.evidence_type} Evidence
                  </span>
                  {isDemo(e) && (
                    <span className="font-mono" style={{ fontSize: 10, color: 'rgba(0,0,0,0.4)', display: 'block', marginTop: 2 }}>
                      [DEMO — simulated]
                    </span>
                  )}
                </div>
                {hasTimestamp && (
                  <span className="font-mono" style={{ fontSize: 11, color: 'rgba(0,0,0,0.5)' }}>
                    {formatDate(e.event_timestamp!)}
                  </span>
                )}
              </div>
              <pre
                className="font-mono"
                style={{
                  fontSize: 12,
                  whiteSpace: 'pre-wrap',
                  margin: 0,
                  color: 'rgba(0,0,0,0.7)',
                }}
              >
                {JSON.stringify(
                  Object.fromEntries(Object.entries(e.content).filter(([k]) => k !== 'note')),
                  null, 2
                )}
              </pre>
              {e.source_id && (
                <div className="font-mono" style={{ fontSize: 10, marginTop: 8, color: 'rgba(0,0,0,0.4)' }}>
                  Source ID: {e.source_id}
                </div>
              )}
            </div>
          </motion.div>
        )
      })}
        {evidenceList.length === 0 && (
           <div className="font-body text-slate" style={{ fontStyle: 'italic' }}>No evidence recorded.</div>
        )}
      </div>
    </div>
  )
}
