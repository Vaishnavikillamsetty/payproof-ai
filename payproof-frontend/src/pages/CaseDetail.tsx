import React, { useState, useEffect } from 'react'
import { api } from '../api'
import type { CaseDetail as CaseDetailType, AuditEntry, EvidenceUploadPayload } from '../types'
import {
  statusTheme,
  getAIRecommendation,
  aiRecommendationLabel,
  isWebhookOrigin,
  isDemoCase,
  formatAmount,
  formatDate,
} from '../utils'
import CompletenessBar from '../components/CompletenessBar'
import EvidencePanel from '../components/EvidencePanel'
import AgentActivity from '../components/AgentActivity'
import ClaimList from '../components/ClaimList'

interface Props {
  caseId: string
  onBack: () => void
}

function shortTxn(id: string) {
  const parts = id.split('_')
  return parts.length > 2 ? parts.slice(0, 3).join('_') : (id.length > 12 ? id.slice(0, 12) + '...' : id)
}

function formatDisputeReason(reason: string) {
  return reason.replace(/_/g, ' ').replace(/\w/g, c => c.toUpperCase())
}

function DataSourceBadge({ fromWebhook, isDemo, txn }: { fromWebhook: boolean; isDemo: boolean; txn: string }) {
  if (isDemo && txn.startsWith('DEMO_SCN_')) {
    const parts = txn.split('_')
    const num = parts[2]
    return (
      <span className="badge" style={{ background: 'var(--color-ink-light)', color: 'var(--color-slate-light)', border: '1px solid var(--color-ink-border)' }}>
        DEMO SCENARIO {num} / 15
      </span>
    )
  }
  if (isDemo) {
    return <span className="badge" style={{ background: 'var(--color-ink-light)', color: 'var(--color-slate-light)', border: '1px solid var(--color-ink-border)' }}>DEMO DATA</span>
  }
  if (fromWebhook) {
    return <span className="badge" style={{ background: 'rgba(63, 167, 150, 0.1)', color: 'var(--color-teal)', border: '1px solid rgba(63, 167, 150, 0.3)' }}>LIVE WEBHOOK</span>
  }
  return <span className="badge" style={{ background: 'var(--color-ink-light)', color: 'var(--color-slate-light)', border: '1px solid var(--color-ink-border)' }}>MANUAL ENTRY</span>
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 16, marginTop: 32 }}>
      {children}
    </h2>
  )
}

export default function CaseDetail({ caseId, onBack }: Props) {
  const [data, setData] = useState<{ case: CaseDetailType; audit: AuditEntry[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewerId, setReviewerId] = useState(() => localStorage.getItem('payproof_reviewer_id') || 'analyst_current')
  const [decisionSubmitting, setDecisionSubmitting] = useState<string | null>(null)
  const [decisionError, setDecisionError] = useState<string | null>(null)
  const [confirmAction, setConfirmAction] = useState<'approve' | 'contest' | 'request_more_evidence' | 'resolve' | 'close' | null>(null)

  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [uploadCategory, setUploadCategory] = useState<'transaction' | 'customer' | 'delivery' | 'merchant'>('delivery')
  const [uploadType, setUploadType] = useState('carrier_proof_of_delivery')
  const [uploadFilename, setUploadFilename] = useState('')
  const [uploadDescription, setUploadDescription] = useState('')
  const [uploadFileBase64, setUploadFileBase64] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const loadData = () => {
    return Promise.all([api.getCase(caseId), api.getAudit(caseId)])
      .then(([c, a]) => {
        setData({ case: c, audit: a })
        setError(null)
        setLoading(false)
      })
      .catch((err: Error) => {
        setError(err.message)
        setLoading(false)
      })
  }

  useEffect(() => {
    let isMounted = true
    let pollInterval: number | undefined

    const poll = () => {
      loadData().then(() => {
        if (!isMounted) return
        if (data?.case?.status === 'new' || data?.case?.status === 'investigating' || data?.case?.status === 'OPEN' || data?.case?.status === 'INVESTIGATING') {
          if (!pollInterval) pollInterval = window.setInterval(poll, 3000)
        } else {
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = undefined
          }
        }
      })
    }

    setLoading(true)
    poll()

    return () => {
      isMounted = false
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [caseId])

  if (loading && !data) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-slate)' }}>
        <div style={{ animation: 'spin 1s linear infinite', display: 'inline-block', marginBottom: 16 }}>â³</div>
        <div className="font-body text-slate">Loading case details...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-red)' }}>
        <div className="font-mono">ERROR</div>
        <div className="font-body">{error}</div>
        <button
          onClick={onBack}
          style={{
            marginTop: 16,
            cursor: 'pointer',
            background: 'transparent',
            border: '1px solid var(--color-red)',
            color: 'var(--color-red)',
            padding: '4px 12px',
            borderRadius: 4,
          }}
        >
          Go Back
        </button>
      </div>
    )
  }

  const c = data.case
  const audit = data.audit
  const fromWebhook = isWebhookOrigin(audit)
  const demo = isDemoCase(c.transaction_id)
  const theme = statusTheme(c.status)
  const aiRec = getAIRecommendation(audit)

  const recStr = c.ai_recommendation || aiRec?.recommended_action || c.status
  const recLabel = aiRecommendationLabel(recStr)
  const recColor =
    recStr === 'contest' || recStr === 'CONTEST' || recStr === 'strong_case'
      ? 'var(--color-teal)'
      : recStr === 'approve' || recStr === 'APPROVE'
        ? 'var(--color-teal)'
        : recStr === 'request_more_evidence' || recStr === 'REQUEST_MORE_EVIDENCE' || recStr === 'weak_case'
          ? 'var(--color-amber)'
          : 'var(--color-red)'

  const strength = (c.evidence_strength || 'NOT_EVALUATED').toUpperCase()
  const strengthColor =
    strength === 'HIGH' ? 'var(--color-teal)' : strength === 'MEDIUM' ? 'var(--color-amber)' : 'var(--color-red)'

  async function handleReviewSubmit(action: 'approve' | 'contest' | 'request_more_evidence') {
    setDecisionSubmitting(action)
    setDecisionError(null)
    try {
      localStorage.setItem('payproof_reviewer_id', reviewerId)
      const updatedCase = await api.reviewCase(c.id, action, reviewNotes, reviewerId)
      const updatedAudit = await api.getAudit(c.id)
      setData({ case: updatedCase, audit: updatedAudit })
      setConfirmAction(null)
      setReviewNotes('')
    } catch (err: any) {
      setDecisionError(err.message || 'Failed to submit review decision')
    } finally {
      setDecisionSubmitting(null)
    }
  }

  async function handleLifecycleAction(action: 'resolve' | 'close') {
    setDecisionSubmitting(action)
    setDecisionError(null)
    try {
      const updatedCase =
        action === 'resolve'
          ? await api.resolveCase(c.id, reviewNotes, reviewerId)
          : await api.closeCase(c.id, reviewNotes, reviewerId)
      const updatedAudit = await api.getAudit(c.id)
      setData({ case: updatedCase, audit: updatedAudit })
      setConfirmAction(null)
      setReviewNotes('')
    } catch (err: any) {
      setDecisionError(err.message || `Failed to ${action} case`)
    } finally {
      setDecisionSubmitting(null)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadFilename(file.name)
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      const b64 = result.includes(',') ? result.split(',')[1] : result
      setUploadFileBase64(b64)
    }
    reader.readAsDataURL(file)
  }

  async function handleUploadSubmit(e: React.FormEvent) {
    e.preventDefault()
    setUploading(true)
    setUploadError(null)
    try {
      const payload: EvidenceUploadPayload = {
        category: uploadCategory,
        evidence_type: uploadType,
        filename: uploadFilename || `${uploadCategory}_document.pdf`,
        description: uploadDescription || `Uploaded ${uploadCategory} document`,
        file_base64: uploadFileBase64 || undefined,
        verification_status: 'VERIFIED',
      }
      await api.uploadEvidence(c.id, payload)
      const [updatedCase, updatedAudit] = await Promise.all([api.getCase(c.id), api.getAudit(c.id)])
      setData({ case: updatedCase, audit: updatedAudit })
      setIsUploadOpen(false)
      setUploadFilename('')
      setUploadDescription('')
      setUploadFileBase64(null)
    } catch (err: any) {
      setUploadError(err.message || 'Evidence upload failed')
    } finally {
      setUploading(false)
    }
  }

  const contradicted = c.claims ? c.claims.filter(claim => claim.verdict === 'contradicted') : []

  return (
    <main style={{ maxWidth: 880, margin: '0 auto', padding: '32px 24px' }}>
      {/* 1. CASE HEADER */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 32, flexWrap: 'wrap' }}>
        <button
          onClick={onBack}
          style={{
            background: 'var(--color-ink-light)', border: '1px solid var(--color-ink-border)',
            padding: '8px 16px', borderRadius: 4, color: 'var(--color-slate)',
            cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 12,
          }}
        >
          â BACK TO DASHBOARD
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
            <h1 className="font-mono" style={{ fontSize: 20, margin: 0, color: 'var(--color-white)', letterSpacing: '0.05em' }}>
              CASE {shortTxn(c.transaction_id)}
            </h1>
            <DataSourceBadge fromWebhook={fromWebhook} isDemo={demo} txn={c.transaction_id} />
            <span className="font-mono" style={{
              fontSize: 10, padding: '3px 8px', borderRadius: 3, letterSpacing: '0.08em',
              background: `color-mix(in srgb, ${theme.dot} 15%, transparent)`, color: theme.dot,
            }}>
              {theme.label}
            </span>
          </div>
          <div className="font-body text-slate" style={{ fontSize: 14, marginBottom: 4 }}>
            <span style={{ color: 'var(--color-white)', fontWeight: 500 }}>{formatAmount(c.amount, c.currency)}</span> â¢ {formatDisputeReason(c.dispute_reason)} â¢ Merchant <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{c.merchant_id.toUpperCase()}</span>
          </div>
          <div className="font-body text-slate-light" style={{ fontSize: 13, fontStyle: 'italic' }}>
            "{c.customer_claim}"
          </div>
        </div>
      </div>

      {/* SECTION A: AI ANALYSIS & RECOMMENDATION */}
      <section style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <SectionHeader>Section A: AI Analysis & Recommendation</SectionHeader>
          <span className="badge" style={{ background: 'rgba(224, 163, 57, 0.1)', color: 'var(--color-amber)', border: '1px solid rgba(224, 163, 57, 0.3)', fontSize: 11 }}>
            ADVISORY ONLY
          </span>
        </div>

        <div className="card" style={{ padding: '24px', borderTop: `4px solid ${recColor}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.1em', marginBottom: 8 }}>
                AI RECOMMENDATION
              </div>
              <div className="font-mono" style={{ fontSize: 24, color: recColor, fontWeight: 700, letterSpacing: '0.02em' }}>
                {recLabel}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', marginBottom: 4 }}>CONFIDENCE</div>
              <div className="font-mono" style={{ fontSize: 20, color: 'var(--color-white)' }}>
                {c.overall_confidence != null ? `${Math.round(c.overall_confidence * 100)}%` : (aiRec?.confidence != null ? `${Math.round(aiRec.confidence * 100)}%` : '---')}
              </div>
            </div>
          </div>

          {c.ai_explanation && (
            <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--color-ink-border)' }}>
              <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>
                Explanation Summary
              </span>
              <p className="font-body text-white" style={{ fontSize: 13, margin: 0, lineHeight: 1.5 }}>
                {c.ai_explanation}
              </p>
            </div>
          )}

          {c.contradiction_detected && (
            <div style={{ marginTop: 16, padding: '12px 14px', borderLeft: '3px solid var(--color-red)', background: 'rgba(214,72,60,0.08)' }}>
              <div className="font-mono" style={{ fontSize: 11, color: 'var(--color-red)', letterSpacing: '0.06em' }}>SECURITY / EVIDENCE CONFLICT DETECTED</div>
              <div className="font-body text-slate" style={{ fontSize: 12, marginTop: 4 }}>Deterministic safety rules require human review; this case is not treated as low risk.</div>
            </div>
          )}

          <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid var(--color-ink-border)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13 }}>â¹ï¸</span>
            <span className="font-body text-slate" style={{ fontSize: 12, fontStyle: 'italic' }}>
              AI recommendation is advisory. Final dispute action requires human review and authorization.
            </span>
          </div>
        </div>
      </section>

      {/* SECTION B: EVIDENCE OVERVIEW & MANAGEMENT */}
      <section style={{ marginBottom: 36 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <SectionHeader>Section B: Evidence Overview & Management</SectionHeader>
          <button
            type="button"
            onClick={() => setIsUploadOpen(true)}
            style={{
              background: 'var(--color-teal)',
              color: 'var(--color-ink-dark)',
              border: 'none',
              padding: '6px 14px',
              borderRadius: 4,
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            + Upload Evidence
          </button>
        </div>

        <div className="card" style={{ padding: '20px', marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Canonical 4-Category Coverage
            </span>
            <span className="font-mono" style={{ fontSize: 11, color: strengthColor, fontWeight: 600 }}>
              Strength: {strength}
            </span>
          </div>
          <CompletenessBar
            score={c.completeness_score}
            showLabel={true}
            showChecklist={true}
            categoriesAvailable={c.categories_available}
            evidence={c.evidence}
          />
        </div>

        <EvidencePanel
          evidenceList={c.evidence}
          audit={audit}
          onUploadClick={() => setIsUploadOpen(true)}
        />
      </section>

      {/* SECTION C: HUMAN REVIEW & FINAL DECISION */}
      <section style={{ marginBottom: 36 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <SectionHeader>Section C: Human Review & Decision</SectionHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="font-mono text-slate" style={{ fontSize: 11 }}>Reviewer:</span>
            <input
              type="text"
              value={reviewerId}
              onChange={(e) => setReviewerId(e.target.value)}
              placeholder="analyst_id"
              style={{
                background: 'var(--color-ink-dark)',
                border: '1px solid var(--color-ink-border)',
                color: 'var(--color-white)',
                padding: '2px 8px',
                borderRadius: 3,
                fontSize: 11,
                fontFamily: 'var(--font-mono)',
                width: 130,
              }}
            />
          </div>
        </div>

        <div className="card" style={{ padding: '24px', borderLeft: '4px solid var(--color-teal)' }}>
          {c.human_decision ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
                <div>
                  <span className="font-mono text-slate" style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                    Recorded Human Decision
                  </span>
                  <div className="font-mono" style={{ fontSize: 22, color: 'var(--color-teal)', fontWeight: 700, marginTop: 4 }}>
                    {c.human_decision.toUpperCase()}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className="font-mono text-slate" style={{ fontSize: 10, display: 'block' }}>DECISION TIMESTAMP</span>
                  <span className="font-mono text-white" style={{ fontSize: 12 }}>
                    {c.decision_timestamp ? formatDate(c.decision_timestamp) : 'Recorded'}
                  </span>
                  <span className="font-mono text-slate" style={{ fontSize: 10, display: 'block', marginTop: 2 }}>
                    By: {c.reviewer_id || reviewerId}
                  </span>
                </div>
              </div>

              {c.reviewer_notes && (
                <div style={{ padding: '12px 14px', background: 'var(--color-ink-dark)', borderRadius: 4, marginBottom: 20 }}>
                  <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>
                    Reviewer Notes
                  </span>
                  <span className="font-body text-slate-light" style={{ fontSize: 13 }}>
                    {c.reviewer_notes}
                  </span>
                </div>
              )}

              <div style={{ paddingTop: 16, borderTop: '1px solid var(--color-ink-border)' }}>
                <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 10 }}>
                  Lifecycle Actions (Final Settlement)
                </span>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  {c.status !== 'RESOLVED' && c.status !== 'resolved' && (
                    <button
                      type="button"
                      onClick={() => setConfirmAction('resolve')}
                      disabled={decisionSubmitting !== null}
                      style={{
                        padding: '8px 16px',
                        background: 'var(--color-teal)',
                        color: 'var(--color-ink-dark)',
                        border: 'none',
                        borderRadius: 4,
                        fontFamily: 'var(--font-mono)',
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      â Mark Case Resolved
                    </button>
                  )}
                  {c.status !== 'CLOSED' && c.status !== 'closed' && (
                    <button
                      type="button"
                      onClick={() => setConfirmAction('close')}
                      disabled={decisionSubmitting !== null}
                      style={{
                        padding: '8px 16px',
                        background: 'transparent',
                        border: '1px solid var(--color-slate)',
                        color: 'var(--color-slate-light)',
                        borderRadius: 4,
                        fontFamily: 'var(--font-mono)',
                        fontSize: 12,
                        cursor: 'pointer',
                      }}
                    >
                      Archive & Close Case
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: 16 }}>
                <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                  Review Notes / Rationale (Audit Record)
                </span>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Explain rationale for this decision (e.g., customer signed delivery manifest verified, merchant agreed to refund)..."
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    background: 'var(--color-ink-dark)',
                    border: '1px solid var(--color-ink-border)',
                    borderRadius: 4,
                    color: 'var(--color-white)',
                    fontSize: 13,
                    fontFamily: 'var(--font-body)',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                <button
                  type="button"
                  onClick={() => setConfirmAction('approve')}
                  disabled={decisionSubmitting !== null}
                  style={{
                    padding: '10px 18px',
                    background: 'transparent',
                    border: '1px solid var(--color-teal)',
                    color: 'var(--color-teal)',
                    borderRadius: 4,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  APPROVE CLAIM (REFUND)
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmAction('contest')}
                  disabled={decisionSubmitting !== null}
                  style={{
                    padding: '10px 18px',
                    background: 'transparent',
                    border: '1px solid var(--color-teal)',
                    color: 'var(--color-teal)',
                    borderRadius: 4,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  CONTEST DISPUTE
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmAction('request_more_evidence')}
                  disabled={decisionSubmitting !== null}
                  style={{
                    padding: '10px 18px',
                    background: 'transparent',
                    border: '1px solid var(--color-amber)',
                    color: 'var(--color-amber)',
                    borderRadius: 4,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  REQUEST MORE EVIDENCE
                </button>
              </div>

              {decisionError && (
                <div className="font-body" style={{ color: 'var(--color-red)', fontSize: 13, marginTop: 12 }}>
                  {decisionError}
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Confirmation Dialog Modal */}
      {confirmAction && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
          }}
        >
          <div className="card" style={{ maxWidth: 440, width: '100%', padding: 24 }}>
            <h3 className="font-mono text-white" style={{ margin: '0 0 12px 0', fontSize: 16 }}>
              Confirm {confirmAction.toUpperCase().replace(/_/g, ' ')}
            </h3>
            <p className="font-body text-slate-light" style={{ fontSize: 13, lineHeight: 1.5, marginBottom: 20 }}>
              Are you sure you want to record this decision? This will append an immutable record to the audit trail with
              reviewer ID <strong style={{ color: 'var(--color-white)' }}>{reviewerId}</strong>.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                type="button"
                onClick={() => setConfirmAction(null)}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--color-ink-border)',
                  color: 'var(--color-slate)',
                  padding: '8px 14px',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={decisionSubmitting !== null}
                onClick={() => {
                  if (confirmAction === 'resolve' || confirmAction === 'close') {
                    handleLifecycleAction(confirmAction)
                  } else {
                    handleReviewSubmit(confirmAction)
                  }
                }}
                style={{
                  background: 'var(--color-teal)',
                  color: 'var(--color-ink-dark)',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                {decisionSubmitting ? 'Recording...' : 'Confirm Decision'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Evidence Upload Modal */}
      {isUploadOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
          }}
        >
          <div className="card" style={{ maxWidth: 500, width: '100%', padding: 24 }}>
            <h3 className="font-mono text-white" style={{ margin: '0 0 16px 0', fontSize: 16 }}>
              Upload Dispute Evidence
            </h3>
            <form onSubmit={handleUploadSubmit}>
              <div style={{ marginBottom: 14 }}>
                <label className="font-mono text-slate" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                  CANONICAL CATEGORY
                </label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value as any)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    background: 'var(--color-ink-dark)',
                    border: '1px solid var(--color-ink-border)',
                    borderRadius: 4,
                    color: 'var(--color-white)',
                    fontSize: 13,
                  }}
                >
                  <option value="transaction">1. Transaction & Payment Records</option>
                  <option value="customer">2. Customer & Authentication Logs</option>
                  <option value="delivery">3. Delivery & Fulfilment Evidence</option>
                  <option value="merchant">4. Merchant Records & Policies</option>
                </select>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label className="font-mono text-slate" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                  EVIDENCE TYPE SLUG
                </label>
                <input
                  type="text"
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value)}
                  placeholder="e.g. proof_of_delivery, chat_log, invoice"
                  required
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    background: 'var(--color-ink-dark)',
                    border: '1px solid var(--color-ink-border)',
                    borderRadius: 4,
                    color: 'var(--color-white)',
                    fontSize: 13,
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div style={{ marginBottom: 14 }}>
                <label className="font-mono text-slate" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                  ATTACH FILE (STORED IN POSTGRESQL)
                </label>
                <input
                  type="file"
                  onChange={handleFileChange}
                  style={{
                    width: '100%',
                    padding: '6px 0',
                    color: 'var(--color-slate-light)',
                    fontSize: 12,
                  }}
                />
              </div>

              <div style={{ marginBottom: 20 }}>
                <label className="font-mono text-slate" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                  DESCRIPTION / CONTEXT
                </label>
                <textarea
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  placeholder="Describe what this document proves..."
                  rows={2}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    background: 'var(--color-ink-dark)',
                    border: '1px solid var(--color-ink-border)',
                    borderRadius: 4,
                    color: 'var(--color-white)',
                    fontSize: 13,
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              {uploadError && (
                <div className="font-body text-red" style={{ fontSize: 12, marginBottom: 12, color: 'var(--color-red)' }}>
                  {uploadError}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(false)}
                  style={{
                    background: 'transparent',
                    border: '1px solid var(--color-ink-border)',
                    color: 'var(--color-slate)',
                    padding: '8px 14px',
                    borderRadius: 4,
                    cursor: 'pointer',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  style={{
                    background: 'var(--color-teal)',
                    color: 'var(--color-ink-dark)',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: 4,
                    cursor: 'pointer',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  {uploading ? 'Uploading...' : 'Save & Attach Evidence'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4. AI INVESTIGATION PIPELINE */}
      <SectionHeader>AI Investigation Pipeline</SectionHeader>
      <AgentActivity audit={audit} />

      {/* 5. CLAIM VERIFICATION */}
      <SectionHeader>Claim Verification</SectionHeader>
      <ClaimList claims={c.claims} audit={audit} />

      {/* 6. CONTRADICTIONS */}
      {contradicted.length > 0 && (
        <>
          <SectionHeader>Contradictions Found</SectionHeader>
          <div style={{ marginBottom: 32 }}>
            {contradicted.map(claim => (
              <div key={claim.id} style={{
                background: 'rgba(214,72,60,0.08)', borderLeft: '4px solid var(--color-red)',
                padding: '16px 20px', borderRadius: '0 6px 6px 0', marginBottom: 10,
              }}>
                <div className="font-mono" style={{ color: 'var(--color-red)', fontSize: 11, letterSpacing: '0.08em', marginBottom: 8 }}>
                  CONTRADICTION DETECTED
                </div>
                <p className="font-body text-white" style={{ fontSize: 14, margin: 0, lineHeight: 1.6 }}>
                  {claim.claim_text}
                </p>
                <div className="font-body text-slate" style={{ fontSize: 12, marginTop: 8 }}>
                  Conflicting evidence found - this case requires human review.
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </main>
  )
}
