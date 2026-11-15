import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../api'
import type { CaseDetail as CaseDetailType, AuditEntry } from '../types'
import { getAIRecommendation } from '../utils'

interface Props {
  c: CaseDetailType
  audit: AuditEntry[]
  isOpen: boolean
  onClose: () => void
  onSuccess: (updatedCase: CaseDetailType) => void
}

export default function HumanReviewModal({ c, audit, isOpen, onClose, onSuccess }: Props) {
  const [action, setAction] = useState<'approve' | 'request_more_evidence' | 'escalate'>('approve')
  const [notes, setNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const aiRec = getAIRecommendation(audit)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    try {
      const updated = await api.reviewCase(c.id, action, notes)
      onSuccess(updated)
      onClose()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: 24,
        }}
        onClick={onClose}
      >
        <motion.div
          initial={{ y: 20, opacity: 0, scale: 0.95 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 20, opacity: 0, scale: 0.95 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          style={{
            background: 'var(--color-ink-light)',
            border: '1px solid var(--color-ink-border)',
            borderRadius: 10,
            width: '100%',
            maxWidth: 520,
            overflow: 'hidden',
            boxShadow: '0 24px 48px rgba(0,0,0,0.5)',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-ink-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 className="font-mono text-white" style={{ margin: 0, fontSize: 14, letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 700 }}>
              Human Review Decision
            </h2>
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--color-slate)',
                cursor: 'pointer',
                fontSize: 18,
                lineHeight: 1,
                padding: '4px 8px',
                borderRadius: 4,
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-white)' }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-slate)' }}
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleSubmit} style={{ padding: 24 }}>
            {aiRec && (
              <div style={{ marginBottom: 24, padding: 16, background: 'var(--color-ink-mid)', borderRadius: 7, border: '1px solid var(--color-ink-border)' }}>
                <div className="font-mono text-slate-light" style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6 }}>
                  AI RECOMMENDATION
                </div>
                <div className="font-mono" style={{ fontSize: 16, color: 'var(--color-teal)', fontWeight: 700, marginBottom: 4 }}>
                  {aiRec.recommended_action.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div className="font-mono text-slate" style={{ fontSize: 11 }}>
                  Confidence: <span style={{ color: 'var(--color-white)' }}>{aiRec.confidence !== null ? Math.round(aiRec.confidence * 100) : '-'}%</span>
                </div>
              </div>
            )}

            <div style={{ marginBottom: 24 }}>
              <div className="font-mono text-slate-light" style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 10 }}>
                SELECT ACTION
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px 14px',
                    background: action === 'approve' ? 'rgba(54,198,174,0.10)' : 'var(--color-ink-mid)',
                    border: `1px solid ${action === 'approve' ? 'var(--color-teal)' : 'var(--color-ink-border)'}`,
                    borderRadius: 7,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input type="radio" name="action" checked={action === 'approve'} onChange={() => setAction('approve')} />
                  <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)', fontWeight: 600 }}>
                    ✓ Approve Recommendation
                  </span>
                </label>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px 14px',
                    background: action === 'request_more_evidence' ? 'rgba(240,168,48,0.10)' : 'var(--color-ink-mid)',
                    border: `1px solid ${action === 'request_more_evidence' ? 'var(--color-amber)' : 'var(--color-ink-border)'}`,
                    borderRadius: 7,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input type="radio" name="action" checked={action === 'request_more_evidence'} onChange={() => setAction('request_more_evidence')} />
                  <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)', fontWeight: 600 }}>
                    Request More Evidence
                  </span>
                </label>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px 14px',
                    background: action === 'escalate' ? 'rgba(224,82,82,0.10)' : 'var(--color-ink-mid)',
                    border: `1px solid ${action === 'escalate' ? 'var(--color-red)' : 'var(--color-ink-border)'}`,
                    borderRadius: 7,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input type="radio" name="action" checked={action === 'escalate'} onChange={() => setAction('escalate')} />
                  <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)', fontWeight: 600 }}>
                    ↑ Escalate
                  </span>
                </label>
              </div>
            </div>

            <div style={{ marginBottom: 24 }}>
              <div className="font-mono text-slate-light" style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>
                REVIEW NOTES
              </div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add internal notes for this decision..."
                style={{
                  width: '100%',
                  background: 'var(--color-ink-mid)',
                  border: '1px solid var(--color-ink-border)',
                  borderRadius: 7,
                  padding: '10px 14px',
                  color: 'var(--color-white)',
                  fontFamily: 'var(--font-body)',
                  fontSize: 13,
                  minHeight: 80,
                  resize: 'vertical',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {error && <div style={{ color: 'var(--color-red)', fontSize: 13, marginBottom: 16 }}>{error}</div>}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                style={{
                  padding: '9px 18px',
                  background: 'var(--color-ink-mid)',
                  border: '1px solid var(--color-ink-border)',
                  color: 'var(--color-slate-light)',
                  borderRadius: 7,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 600,
                  transition: 'background 0.15s ease, color 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = '#1E2D45'
                  ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-white)'
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = 'var(--color-ink-mid)'
                  ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-slate-light)'
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                style={{
                  padding: '9px 20px',
                  background: 'var(--color-teal)',
                  border: 'none',
                  color: '#0B1120',
                  borderRadius: 7,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: '0.04em',
                  boxShadow: '0 2px 8px rgba(54,198,174,0.3)',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal-dim)' }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal)' }}
              >
                {isSubmitting ? 'Submitting...' : 'Confirm Review'}
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
