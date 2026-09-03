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
          background: 'rgba(0,0,0,0.6)',
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
            background: 'var(--color-ink)',
            border: '1px solid var(--color-ink-border)',
            borderRadius: 12,
            width: '100%',
            maxWidth: 500,
            overflow: 'hidden',
            boxShadow: '0 24px 48px rgba(0,0,0,0.4)'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-ink-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 className="font-mono" style={{ margin: 0, fontSize: 14, textTransform: 'uppercase', color: 'var(--color-white)' }}>
              Human Review Decision
            </h2>
            <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--color-slate)', cursor: 'pointer', fontSize: 20, lineHeight: 1 }}>?</button>
          </div>

          <form onSubmit={handleSubmit} style={{ padding: 24 }}>
            {aiRec && (
              <div style={{ marginBottom: 24, padding: 16, background: 'rgba(91,107,124,0.1)', borderRadius: 6, border: '1px solid rgba(91,107,124,0.2)' }}>
                <div className="font-mono text-slate" style={{ fontSize: 11, marginBottom: 8 }}>AI RECOMMENDATION</div>
                <div className="font-mono" style={{ fontSize: 14, color: 'var(--color-white)', fontWeight: 600, marginBottom: 4 }}>
                  {aiRec.recommended_action.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div className="font-mono text-slate" style={{ fontSize: 11 }}>
                  Confidence: {aiRec.confidence !== null ? Math.round(aiRec.confidence * 100) : '-'}%
                </div>
              </div>
            )}

            <div style={{ marginBottom: 24 }}>
              <div className="font-mono text-slate" style={{ fontSize: 11, marginBottom: 12 }}>SELECT ACTION</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, background: 'var(--color-ink-light)', border: `1px solid ${action === 'approve' ? 'var(--color-teal)' : 'var(--color-ink-border)'}`, borderRadius: 6, cursor: 'pointer' }}>
                  <input type="radio" name="action" checked={action === 'approve'} onChange={() => setAction('approve')} />
                  <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>? Approve Recommendation</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, background: 'var(--color-ink-light)', border: `1px solid ${action === 'request_more_evidence' ? 'var(--color-amber)' : 'var(--color-ink-border)'}`, borderRadius: 6, cursor: 'pointer' }}>
                  <input type="radio" name="action" checked={action === 'request_more_evidence'} onChange={() => setAction('request_more_evidence')} />
                  <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>Request More Evidence</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, background: 'var(--color-ink-light)', border: `1px solid ${action === 'escalate' ? 'var(--color-red)' : 'var(--color-ink-border)'}`, borderRadius: 6, cursor: 'pointer' }}>
                  <input type="radio" name="action" checked={action === 'escalate'} onChange={() => setAction('escalate')} />
                  <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>? Escalate</span>
                </label>
              </div>
            </div>

            <div style={{ marginBottom: 24 }}>
              <div className="font-mono text-slate" style={{ fontSize: 11, marginBottom: 8 }}>REVIEW NOTES</div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add internal notes for this decision..."
                style={{
                  width: '100%',
                  background: 'var(--color-ink-light)',
                  border: '1px solid var(--color-ink-border)',
                  borderRadius: 6,
                  padding: 12,
                  color: 'var(--color-white)',
                  fontFamily: 'var(--font-body)',
                  fontSize: 14,
                  minHeight: 80,
                  resize: 'vertical'
                }}
              />
            </div>

            {error && <div style={{ color: 'var(--color-red)', fontSize: 13, marginBottom: 16 }}>{error}</div>}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                style={{ padding: '8px 16px', background: 'transparent', border: '1px solid var(--color-ink-border)', color: 'var(--color-white)', borderRadius: 4, cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 12 }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                style={{ padding: '8px 16px', background: 'var(--color-teal)', border: 'none', color: '#000', borderRadius: 4, cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600 }}
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
