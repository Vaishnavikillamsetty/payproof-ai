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


function formatDisputeReason(reason: string) {
  return reason.replace(/_/g, ' ').replace(/ \w/g, (c) => c.toUpperCase())
}

function DataSourceBadge({ fromWebhook, isDemo, txn }: { fromWebhook: boolean; isDemo: boolean; txn: string }) {
  if (isDemo && txn.startsWith('DEMO_SCN_')) {
    const parts = txn.split('_')
    const num = parts[2]
    return (
      <span
        className="badge font-mono"
        style={{
          background: 'rgba(100, 116, 139, 0.12)',
          color: 'var(--color-slate-light)',
          border: '1px solid var(--color-ink-border)',
        }}
      >
        DEMO SCENARIO {num} / 15
      </span>
    )
  }
  if (isDemo) {
    return (
      <span
        className="badge font-mono"
        style={{
          background: 'rgba(100, 116, 139, 0.12)',
          color: 'var(--color-slate-light)',
          border: '1px solid var(--color-ink-border)',
        }}
      >
        DEMO DATA
      </span>
    )
  }
  if (fromWebhook) {
    return (
      <span
        className="badge font-mono"
        style={{
          background: 'rgba(54, 198, 174, 0.12)',
          color: 'var(--color-teal)',
          border: '1px solid rgba(54, 198, 174, 0.3)',
        }}
      >
        LIVE WEBHOOK
      </span>
    )
  }
  return (
    <span
      className="badge font-mono"
      style={{
        background: 'rgba(100, 116, 139, 0.12)',
        color: 'var(--color-slate-light)',
        border: '1px solid var(--color-ink-border)',
      }}
    >
      MANUAL ENTRY
    </span>
  )
}

function SectionHeader({
  badge,
  title,
  subtitle,
  action,
}: {
  badge?: string
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 14,
        flexWrap: 'wrap',
        gap: 8,
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 3, height: 16, background: 'var(--color-teal)', borderRadius: 2, flexShrink: 0 }} />
          <h2
            className="font-mono text-white"
            style={{
              fontSize: 13,
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              margin: 0,
            }}
          >
            {title}
          </h2>
          {badge && (
            <span
              className="badge"
              style={{
                fontSize: 10,
                padding: '2px 7px',
                background: 'rgba(240, 168, 48, 0.12)',
                color: 'var(--color-amber)',
                border: '1px solid rgba(240, 168, 48, 0.25)',
              }}
            >
              {badge}
            </span>
          )}
        </div>
        {subtitle && (
          <p className="font-body text-slate" style={{ fontSize: 12, margin: '4px 0 0 11px' }}>
            {subtitle}
          </p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

export default function CaseDetail({ caseId, onBack }: Props) {
  const [data, setData] = useState<{ case: CaseDetailType; audit: AuditEntry[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewerId, setReviewerId] = useState(
    () => localStorage.getItem('payproof_reviewer_id') || 'analyst_current'
  )
  const [decisionSubmitting, setDecisionSubmitting] = useState<string | null>(null)
  const [decisionError, setDecisionError] = useState<string | null>(null)
  const [confirmAction, setConfirmAction] = useState<
    'approve' | 'contest' | 'request_more_evidence' | 'resolve' | 'close' | null
  >(null)

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
        if (
          data?.case?.status === 'new' ||
          data?.case?.status === 'investigating' ||
          data?.case?.status === 'OPEN' ||
          data?.case?.status === 'INVESTIGATING'
        ) {
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
      <div style={{ padding: '80px 24px', textAlign: 'center', color: 'var(--color-slate)' }}>
        <div
          style={{
            width: 24,
            height: 24,
            border: '2px solid var(--color-ink-border)',
            borderTopColor: 'var(--color-teal)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '0 auto 16px',
          }}
        />
        <div className="font-mono text-white" style={{ fontSize: 13, letterSpacing: '0.06em' }}>
          LOADING INVESTIGATION WORKSPACE...
        </div>
        <div className="font-body text-slate" style={{ fontSize: 12, marginTop: 4 }}>
          Retrieving dispute record, evidence graph, and audit trail
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <main style={{ maxWidth: 640, margin: '60px auto', padding: '0 24px' }}>
        <div
          className="card"
          style={{
            padding: 32,
            textAlign: 'center',
            borderLeft: '4px solid var(--color-red)',
            background: 'rgba(224, 82, 82, 0.05)',
          }}
        >
          <div className="font-mono text-red" style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>
            UNABLE TO LOAD CASE FILE
          </div>
          <p className="font-body text-slate-light" style={{ fontSize: 14, marginBottom: 20 }}>
            {error || 'Case not found'}
          </p>
          <button
            onClick={onBack}
            style={{
              cursor: 'pointer',
              background: 'var(--color-ink-mid)',
              border: '1px solid var(--color-ink-border)',
              color: 'var(--color-white)',
              padding: '9px 20px',
              borderRadius: 6,
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            ← Back to Dashboard
          </button>
        </div>
      </main>
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

  const confidencePct =
    c.overall_confidence != null
      ? Math.round(c.overall_confidence * 100)
      : aiRec?.confidence != null
        ? Math.round(aiRec.confidence * 100)
        : null

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

  const contradicted = c.claims ? c.claims.filter((claim) => claim.verdict === 'contradicted') : []

  return (
    <main style={{ maxWidth: 1240, margin: '0 auto', padding: '24px 20px 48px' }}>
      {/* ── TOP UTILITY BAR: Back + Badges ── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 16,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <button
          onClick={onBack}
          style={{
            background: 'var(--color-ink-mid)',
            border: '1px solid var(--color-ink-border)',
            padding: '8px 16px',
            borderRadius: 7,
            color: 'var(--color-slate-light)',
            cursor: 'pointer',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: '0.04em',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-white)'
            ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-slate)'
          }}
          onMouseLeave={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-slate-light)'
            ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-ink-border)'
          }}
        >
          ← Back to Dashboard
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <DataSourceBadge fromWebhook={fromWebhook} isDemo={demo} txn={c.transaction_id} />
          <span
            className="font-mono"
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: '3px 10px',
              borderRadius: 5,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              background: `color-mix(in srgb, ${theme.dot} 14%, transparent)`,
              color: theme.dot,
              border: `1px solid color-mix(in srgb, ${theme.dot} 30%, transparent)`,
            }}
          >
            {theme.label}
          </span>
          {c.contradiction_detected && (
            <span
              className="badge"
              style={{
                background: 'rgba(224, 82, 82, 0.15)',
                color: 'var(--color-red)',
                border: '1px solid rgba(224, 82, 82, 0.35)',
              }}
            >
              ⚠ CONTRADICTION DETECTED
            </span>
          )}
        </div>
      </div>

      {/* ── INVESTIGATION WORKSPACE HEADER CARD ── */}
      <div
        className="card"
        style={{
          padding: '22px 26px',
          marginBottom: 20,
          background: 'linear-gradient(180deg, #141E2D 0%, #0F1624 100%)',
          border: '1px solid var(--color-ink-border)',
          borderRadius: 10,
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.35)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 20 }}>
          {/* Left Metadata Block */}
          <div style={{ flex: 1, minWidth: 280 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
              <span
                className="font-mono text-slate"
                style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 600 }}
              >
                Case File
              </span>
              <span
                className="font-mono"
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: 'var(--color-teal)',
                  background: 'rgba(54, 198, 174, 0.08)',
                  padding: '2px 8px',
                  borderRadius: 5,
                  border: '1px solid rgba(54, 198, 174, 0.25)',
                  letterSpacing: '0.04em',
                }}
              >
                {c.transaction_id}
              </span>
            </div>

            <h1
              className="font-body text-white"
              style={{
                fontSize: 24,
                fontWeight: 700,
                margin: '0 0 10px 0',
                lineHeight: 1.25,
                letterSpacing: '-0.01em',
              }}
            >
              {formatDisputeReason(c.dispute_reason)}
            </h1>

            {/* Context pills strip */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', fontSize: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span className="font-mono text-slate" style={{ textTransform: 'uppercase', fontSize: 11 }}>
                  Merchant:
                </span>
                <span className="font-mono text-white" style={{ fontWeight: 600 }}>
                  {c.merchant_id.toUpperCase()}
                </span>
              </div>
              <span style={{ color: 'var(--color-ink-border)' }}>•</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span className="font-mono text-slate" style={{ textTransform: 'uppercase', fontSize: 11 }}>
                  Dispute Filed:
                </span>
                <span className="font-mono text-slate-light">{formatDate(c.created_at)}</span>
              </div>
              {c.decision_timestamp && (
                <>
                  <span style={{ color: 'var(--color-ink-border)' }}>•</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span className="font-mono text-slate" style={{ textTransform: 'uppercase', fontSize: 11 }}>
                      Decided:
                    </span>
                    <span className="font-mono text-slate-light">{formatDate(c.decision_timestamp)}</span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Right Highlight Box: Amount At Risk */}
          <div
            style={{
              background: 'var(--color-ink)',
              border: '1px solid var(--color-ink-border)',
              borderRadius: 8,
              padding: '12px 20px',
              textAlign: 'right',
              minWidth: 190,
              boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
            }}
          >
            <span
              className="font-mono text-slate"
              style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', display: 'block', marginBottom: 2 }}
            >
              Dispute Amount
            </span>
            <div
              className="font-mono text-white"
              style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.15 }}
            >
              {formatAmount(c.amount, c.currency)}
            </div>
            <span
              className="font-mono"
              style={{ fontSize: 11, color: 'var(--color-teal)', fontWeight: 600, marginTop: 4, display: 'block' }}
            >
              {c.currency || 'USD'} Capital Exposure
            </span>
          </div>
        </div>

        {/* Customer claim statement callout */}
        <div
          style={{
            marginTop: 18,
            padding: '12px 16px',
            background: 'var(--color-ink-mid)',
            borderRadius: 7,
            borderLeft: '3px solid var(--color-teal)',
            border: '1px solid var(--color-ink-border)',
            borderLeftWidth: 3,
            borderLeftColor: 'var(--color-teal)',
          }}
        >
          <div
            className="font-mono text-slate"
            style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600, marginBottom: 3 }}
          >
            Customer Claim Statement (Allegation)
          </div>
          <p
            className="font-body text-white"
            style={{ fontSize: 13, margin: 0, lineHeight: 1.5, opacity: 0.92, fontStyle: 'italic' }}
          >
            "{c.customer_claim}"
          </p>
        </div>
      </div>

      {/* ── CASE OVERVIEW: 4 COMPACT SUMMARY CARDS ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
        {/* Card 1: AI Recommendation */}
        <div
          className="card"
          style={{
            padding: '14px 16px',
            borderLeft: `3px solid ${recColor}`,
            background: 'var(--color-ink-light)',
          }}
        >
          <span
            className="font-mono text-slate"
            style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 4 }}
          >
            AI Recommendation
          </span>
          <div
            className="font-mono"
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: recColor,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              letterSpacing: '0.02em',
            }}
          >
            {recLabel}
          </div>
          <span className="font-body text-slate-light" style={{ fontSize: 11, marginTop: 3, display: 'block' }}>
            Advisory Pipeline
          </span>
        </div>

        {/* Card 2: AI Confidence */}
        <div className="card" style={{ padding: '14px 16px', background: 'var(--color-ink-light)' }}>
          <span
            className="font-mono text-slate"
            style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 4 }}
          >
            AI Confidence
          </span>
          <div className="font-mono text-white" style={{ fontSize: 18, fontWeight: 700 }}>
            {confidencePct !== null ? `${confidencePct}%` : '---'}
          </div>
          <span className="font-body text-slate-light" style={{ fontSize: 11, marginTop: 3, display: 'block' }}>
            {aiRec?.used_fallback ? 'Fallback Policy' : 'Evidence-weighted model'}
          </span>
        </div>

        {/* Card 3: Evidence Strength */}
        <div className="card" style={{ padding: '14px 16px', background: 'var(--color-ink-light)' }}>
          <span
            className="font-mono text-slate"
            style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 4 }}
          >
            Evidence Strength
          </span>
          <div className="font-mono" style={{ fontSize: 18, fontWeight: 700, color: strengthColor }}>
            {strength}
          </div>
          <span className="font-body text-slate-light" style={{ fontSize: 11, marginTop: 3, display: 'block' }}>
            {c.completeness_score != null
              ? `${Math.round(c.completeness_score)}% completeness score`
              : `${c.categories_available?.length || 0}/4 categories mapped`}
          </span>
        </div>

        {/* Card 4: Human Review Status */}
        <div className="card" style={{ padding: '14px 16px', background: 'var(--color-ink-light)' }}>
          <span
            className="font-mono text-slate"
            style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 4 }}
          >
            Human Review
          </span>
          <div
            className="font-mono"
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: c.human_decision ? 'var(--color-teal)' : 'var(--color-amber)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              letterSpacing: '0.02em',
            }}
          >
            {c.human_decision ? c.human_decision.toUpperCase() : 'PENDING'}
          </div>
          <span className="font-body text-slate-light" style={{ fontSize: 11, marginTop: 3, display: 'block' }}>
            {c.human_decision
              ? c.reviewer_id
                ? `Authorized by ${c.reviewer_id}`
                : 'Decision logged'
              : 'Awaiting human authorization'}
          </span>
        </div>
      </div>

      {/* ── TWO-COLUMN INVESTIGATION WORKSPACE ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ══════════════════════════════════════════════════════════════════════
            LEFT COLUMN (7 cols / ~58%): Evidence, AI Findings, and Claims
        ════════════════════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          {/* SECTION A: AI ANALYSIS & RECOMMENDATION */}
          <section>
            <SectionHeader
              title="Section A: AI Analysis & Recommendation"
              badge="ADVISORY ONLY"
              subtitle="Algorithmic finding based on merchant records and customer claim veracity"
            />

            <div
              className="card"
              style={{
                padding: '22px 24px',
                borderTop: `4px solid ${recColor}`,
                background: 'var(--color-ink-light)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
                <div>
                  <div
                    className="font-mono text-slate"
                    style={{ fontSize: 11, letterSpacing: '0.08em', marginBottom: 4, textTransform: 'uppercase' }}
                  >
                    Recommended Action
                  </div>
                  <div
                    className="font-mono"
                    style={{ fontSize: 24, color: recColor, fontWeight: 700, letterSpacing: '0.02em' }}
                  >
                    {recLabel}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div
                    className="font-mono text-slate"
                    style={{ fontSize: 11, letterSpacing: '0.06em', marginBottom: 4, textTransform: 'uppercase' }}
                  >
                    Engine Confidence
                  </div>
                  <div className="font-mono text-white" style={{ fontSize: 22, fontWeight: 700 }}>
                    {confidencePct !== null ? `${confidencePct}%` : '---'}
                  </div>
                </div>
              </div>

              {c.ai_explanation && (
                <div
                  style={{
                    marginTop: 16,
                    paddingTop: 14,
                    borderTop: '1px solid var(--color-ink-border)',
                  }}
                >
                  <span
                    className="font-mono text-slate-light"
                    style={{
                      fontSize: 10,
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      display: 'block',
                      marginBottom: 6,
                      fontWeight: 600,
                    }}
                  >
                    Explanation Summary
                  </span>
                  <p className="font-body text-white" style={{ fontSize: 13, margin: 0, lineHeight: 1.6, opacity: 0.95 }}>
                    {c.ai_explanation}
                  </p>
                </div>
              )}

              {c.contradiction_detected && (
                <div
                  style={{
                    marginTop: 16,
                    padding: '12px 16px',
                    borderLeft: '3px solid var(--color-red)',
                    background: 'rgba(224, 82, 82, 0.08)',
                    borderRadius: '0 6px 6px 0',
                    border: '1px solid rgba(224, 82, 82, 0.25)',
                    borderLeftWidth: 3,
                    borderLeftColor: 'var(--color-red)',
                  }}
                >
                  <div
                    className="font-mono"
                    style={{ fontSize: 11, color: 'var(--color-red)', letterSpacing: '0.06em', fontWeight: 700 }}
                  >
                    SECURITY / EVIDENCE CONFLICT DETECTED
                  </div>
                  <div className="font-body text-slate-light" style={{ fontSize: 12, marginTop: 4, lineHeight: 1.5 }}>
                    Deterministic safety rules require human review; this case cannot be auto-resolved.
                  </div>
                </div>
              )}

              <div
                style={{
                  marginTop: 16,
                  paddingTop: 12,
                  borderTop: '1px solid var(--color-ink-border)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{ fontSize: 13 }}>ℹ️</span>
                <span className="font-body text-slate" style={{ fontSize: 12, fontStyle: 'italic' }}>
                  AI recommendation is advisory. Final dispute action requires human review and authorization.
                </span>
              </div>
            </div>
          </section>

          {/* SECTION B: EVIDENCE OVERVIEW & MANAGEMENT */}
          <section>
            <SectionHeader
              title="Section B: Evidence Overview & Management"
              subtitle="Canonical 4-category evidence coverage and file attachments"
              action={
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(true)}
                  style={{
                    background: 'var(--color-teal)',
                    color: '#0B1120',
                    border: 'none',
                    padding: '7px 15px',
                    borderRadius: 6,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                    cursor: 'pointer',
                    boxShadow: '0 2px 8px rgba(54, 198, 174, 0.25)',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal-dim)'
                  }}
                  onMouseLeave={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal)'
                  }}
                >
                  + Upload Evidence
                </button>
              }
            />

            <div className="card" style={{ padding: '18px 20px', marginBottom: 16, background: 'var(--color-ink-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span
                  className="font-mono text-slate"
                  style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600 }}
                >
                  Canonical 4-Category Coverage
                </span>
                <span
                  className="font-mono"
                  style={{
                    fontSize: 11,
                    color: strengthColor,
                    fontWeight: 700,
                    background: `color-mix(in srgb, ${strengthColor} 12%, transparent)`,
                    padding: '2px 8px',
                    borderRadius: 4,
                  }}
                >
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

            <EvidencePanel evidenceList={c.evidence} audit={audit} onUploadClick={() => setIsUploadOpen(true)} />
          </section>

          {/* SECTION: CLAIM VERIFICATION */}
          <section>
            <SectionHeader
              title="Claim Verification"
              subtitle="Atomic factual claims evaluated against verified evidence files"
            />
            <ClaimList claims={c.claims} audit={audit} />
          </section>
        </div>

        {/* ══════════════════════════════════════════════════════════════════════
            RIGHT COLUMN (5 cols / ~42%): Human Review Workspace & Pipeline
        ════════════════════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* SECTION C: HUMAN REVIEW & FINAL DECISION WORKSPACE */}
          <section>
            <SectionHeader
              title="Section C: Human Review & Decision"
              subtitle="Reviewer authorization and dispute resolution actions"
            />

            <div
              className="card"
              style={{
                padding: '22px 24px',
                borderLeft: '4px solid var(--color-teal)',
                background: 'var(--color-ink-light)',
                boxShadow: '0 2px 12px rgba(0,0,0,0.3)',
              }}
            >
              {/* Reviewer Identifier Bar */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 18,
                  paddingBottom: 14,
                  borderBottom: '1px solid var(--color-ink-border)',
                }}
              >
                <span
                  className="font-mono text-slate-light"
                  style={{ fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600 }}
                >
                  Active Reviewer:
                </span>
                <input
                  type="text"
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  placeholder="analyst_id"
                  style={{
                    background: 'var(--color-ink-mid)',
                    border: '1px solid var(--color-ink-border)',
                    color: 'var(--color-white)',
                    padding: '5px 10px',
                    borderRadius: 6,
                    fontSize: 11,
                    fontFamily: 'var(--font-mono)',
                    width: 150,
                  }}
                />
              </div>

              {c.human_decision ? (
                <div>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      flexWrap: 'wrap',
                      gap: 12,
                      marginBottom: 16,
                    }}
                  >
                    <div>
                      <span
                        className="font-mono text-slate"
                        style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase' }}
                      >
                        Recorded Decision
                      </span>
                      <div
                        className="font-mono"
                        style={{ fontSize: 22, color: 'var(--color-teal)', fontWeight: 700, marginTop: 4 }}
                      >
                        {c.human_decision.toUpperCase()}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className="font-mono text-slate" style={{ fontSize: 10, display: 'block' }}>
                        DECISION TIMESTAMP
                      </span>
                      <span className="font-mono text-white" style={{ fontSize: 12 }}>
                        {c.decision_timestamp ? formatDate(c.decision_timestamp) : 'Recorded'}
                      </span>
                      <span className="font-mono text-slate" style={{ fontSize: 10, display: 'block', marginTop: 2 }}>
                        By: {c.reviewer_id || reviewerId}
                      </span>
                    </div>
                  </div>

                  {c.reviewer_notes && (
                    <div
                      style={{
                        padding: '12px 14px',
                        background: 'var(--color-ink-mid)',
                        borderRadius: 6,
                        marginBottom: 20,
                        border: '1px solid var(--color-ink-border)',
                      }}
                    >
                      <span
                        className="font-mono text-slate"
                        style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 4 }}
                      >
                        Reviewer Notes
                      </span>
                      <span className="font-body text-slate-light" style={{ fontSize: 13, lineHeight: 1.5 }}>
                        {c.reviewer_notes}
                      </span>
                    </div>
                  )}

                  <div style={{ paddingTop: 16, borderTop: '1px solid var(--color-ink-border)' }}>
                    <span
                      className="font-mono text-slate"
                      style={{
                        fontSize: 11,
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        display: 'block',
                        marginBottom: 10,
                        fontWeight: 600,
                      }}
                    >
                      Lifecycle Actions (Settlement)
                    </span>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      {c.status !== 'RESOLVED' && c.status !== 'resolved' && (
                        <button
                          type="button"
                          onClick={() => setConfirmAction('resolve')}
                          disabled={decisionSubmitting !== null}
                          style={{
                            padding: '9px 18px',
                            background: 'var(--color-teal)',
                            color: '#0B1120',
                            border: 'none',
                            borderRadius: 6,
                            fontFamily: 'var(--font-mono)',
                            fontSize: 12,
                            fontWeight: 700,
                            letterSpacing: '0.04em',
                            cursor: 'pointer',
                            boxShadow: '0 2px 8px rgba(54,198,174,0.25)',
                            transition: 'all 0.15s ease',
                          }}
                          onMouseEnter={(e) => {
                            ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal-dim)'
                          }}
                          onMouseLeave={(e) => {
                            ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal)'
                          }}
                        >
                          ✓ Mark Case Resolved
                        </button>
                      )}
                      {c.status !== 'CLOSED' && c.status !== 'closed' && (
                        <button
                          type="button"
                          onClick={() => setConfirmAction('close')}
                          disabled={decisionSubmitting !== null}
                          style={{
                            padding: '9px 18px',
                            background: 'var(--color-ink-mid)',
                            border: '1px solid var(--color-ink-border)',
                            color: 'var(--color-slate-light)',
                            borderRadius: 6,
                            fontFamily: 'var(--font-mono)',
                            fontSize: 12,
                            fontWeight: 600,
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                          onMouseEnter={(e) => {
                            ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-white)'
                            ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-slate)'
                          }}
                          onMouseLeave={(e) => {
                            ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-slate-light)'
                            ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-ink-border)'
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
                    <span
                      className="font-mono text-slate"
                      style={{
                        fontSize: 11,
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        display: 'block',
                        marginBottom: 6,
                        fontWeight: 600,
                      }}
                    >
                      Review Notes / Rationale (Audit Record)
                    </span>
                    <textarea
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      placeholder="Explain rationale for this decision (e.g., customer signed delivery manifest verified, merchant agreed to refund)..."
                      rows={3}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        background: 'var(--color-ink-mid)',
                        border: '1px solid var(--color-ink-border)',
                        borderRadius: 7,
                        color: 'var(--color-white)',
                        fontSize: 13,
                        fontFamily: 'var(--font-body)',
                        boxSizing: 'border-box' as const,
                        resize: 'vertical' as const,
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <button
                      type="button"
                      onClick={() => setConfirmAction('approve')}
                      disabled={decisionSubmitting !== null}
                      style={{
                        width: '100%',
                        padding: '11px 18px',
                        background: 'rgba(54, 198, 174, 0.12)',
                        border: '1px solid var(--color-teal)',
                        color: 'var(--color-teal)',
                        borderRadius: 7,
                        fontFamily: 'var(--font-mono)',
                        fontSize: 12,
                        fontWeight: 700,
                        cursor: 'pointer',
                        letterSpacing: '0.06em',
                        textTransform: 'uppercase',
                        transition: 'background 0.15s ease',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                      }}
                      onMouseEnter={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(54, 198, 174, 0.22)'
                      }}
                      onMouseLeave={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(54, 198, 174, 0.12)'
                      }}
                    >
                      ✓ Approve Claim (Refund Customer)
                    </button>

                    <button
                      type="button"
                      onClick={() => setConfirmAction('contest')}
                      disabled={decisionSubmitting !== null}
                      style={{
                        width: '100%',
                        padding: '11px 18px',
                        background: 'rgba(54, 198, 174, 0.05)',
                        border: '1px solid var(--color-teal)',
                        color: 'var(--color-teal)',
                        borderRadius: 7,
                        fontFamily: 'var(--font-mono)',
                        fontSize: 12,
                        fontWeight: 700,
                        cursor: 'pointer',
                        letterSpacing: '0.06em',
                        textTransform: 'uppercase',
                        transition: 'background 0.15s ease',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                      }}
                      onMouseEnter={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(54, 198, 174, 0.16)'
                      }}
                      onMouseLeave={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(54, 198, 174, 0.05)'
                      }}
                    >
                      Contest Dispute (Representment)
                    </button>

                    <button
                      type="button"
                      onClick={() => setConfirmAction('request_more_evidence')}
                      disabled={decisionSubmitting !== null}
                      style={{
                        width: '100%',
                        padding: '11px 18px',
                        background: 'rgba(240, 168, 48, 0.08)',
                        border: '1px solid var(--color-amber)',
                        color: 'var(--color-amber)',
                        borderRadius: 7,
                        fontFamily: 'var(--font-mono)',
                        fontSize: 12,
                        fontWeight: 700,
                        cursor: 'pointer',
                        letterSpacing: '0.06em',
                        textTransform: 'uppercase',
                        transition: 'background 0.15s ease',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                      }}
                      onMouseEnter={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(240, 168, 48, 0.18)'
                      }}
                      onMouseLeave={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(240, 168, 48, 0.08)'
                      }}
                    >
                      Request More Evidence
                    </button>
                  </div>

                  {decisionError && (
                    <div className="font-body text-red" style={{ fontSize: 13, marginTop: 12, color: 'var(--color-red)' }}>
                      {decisionError}
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          {/* CONTRADICTIONS CALLOUT (If Present) */}
          {contradicted.length > 0 && (
            <section>
              <SectionHeader title="Contradictions Found" badge="SECURITY ALERT" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {contradicted.map((claim) => (
                  <div
                    key={claim.id}
                    style={{
                      background: 'rgba(224, 82, 82, 0.08)',
                      border: '1px solid rgba(224, 82, 82, 0.3)',
                      borderLeft: '4px solid var(--color-red)',
                      padding: '14px 18px',
                      borderRadius: '0 8px 8px 0',
                    }}
                  >
                    <div
                      className="font-mono"
                      style={{ color: 'var(--color-red)', fontSize: 11, letterSpacing: '0.08em', marginBottom: 6, fontWeight: 700 }}
                    >
                      CONTRADICTION DETECTED
                    </div>
                    <p className="font-body text-white" style={{ fontSize: 13, margin: 0, lineHeight: 1.5 }}>
                      {claim.claim_text}
                    </p>
                    <div className="font-body text-slate" style={{ fontSize: 12, marginTop: 6 }}>
                      Conflicting evidence identified — case requires human analyst review.
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* AI INVESTIGATION PIPELINE AUDIT LOG */}
          <section>
            <SectionHeader
              title="AI Investigation Pipeline"
              subtitle="Tool execution history and deterministic rule evaluations"
            />
            <AgentActivity audit={audit} />
          </section>
        </div>
      </div>

      {/* ── MODALS ── */}

      {/* Confirmation Dialog Modal */}
      {confirmAction && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: 460,
              width: '100%',
              padding: 28,
              boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
              border: '1px solid var(--color-ink-border)',
              background: 'var(--color-ink-light)',
            }}
          >
            <h3 className="font-mono text-white" style={{ margin: '0 0 12px 0', fontSize: 16, letterSpacing: '0.04em' }}>
              Confirm {confirmAction.toUpperCase().replace(/_/g, ' ')}
            </h3>
            <p className="font-body text-slate-light" style={{ fontSize: 13, lineHeight: 1.6, marginBottom: 24 }}>
              Are you sure you want to record this decision? This will append an immutable record to the audit trail with
              reviewer ID <strong style={{ color: 'var(--color-white)' }}>{reviewerId}</strong>.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button
                type="button"
                onClick={() => setConfirmAction(null)}
                style={{
                  background: 'var(--color-ink-mid)',
                  border: '1px solid var(--color-ink-border)',
                  color: 'var(--color-slate-light)',
                  padding: '9px 18px',
                  borderRadius: 7,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 600,
                  transition: 'background 0.15s ease, color 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  ;(e.currentTarget as HTMLButtonElement).style.background = '#1E2D45'
                  ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-white)'
                }}
                onMouseLeave={(e) => {
                  ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-ink-mid)'
                  ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-slate-light)'
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
                  color: '#0B1120',
                  border: 'none',
                  padding: '9px 20px',
                  borderRadius: 7,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: '0.04em',
                  boxShadow: '0 2px 8px rgba(54,198,174,0.3)',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal-dim)'
                }}
                onMouseLeave={(e) => {
                  ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal)'
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
            background: 'rgba(0,0,0,0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: 520,
              width: '100%',
              padding: 28,
              boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
              border: '1px solid var(--color-ink-border)',
              background: 'var(--color-ink-light)',
            }}
          >
            <h3 className="font-mono text-white" style={{ margin: '0 0 18px 0', fontSize: 16, letterSpacing: '0.04em' }}>
              Upload Dispute Evidence
            </h3>
            <form onSubmit={handleUploadSubmit}>
              <div style={{ marginBottom: 16 }}>
                <label
                  className="font-mono text-slate-light"
                  style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: '0.06em', textTransform: 'uppercase' }}
                >
                  Canonical Category
                </label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value as any)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    background: 'var(--color-ink-mid)',
                    border: '1px solid var(--color-ink-border)',
                    borderRadius: 7,
                    color: 'var(--color-white)',
                    fontSize: 13,
                    fontFamily: 'var(--font-body)',
                  }}
                >
                  <option value="transaction">1. Transaction & Payment Records</option>
                  <option value="customer">2. Customer & Authentication Logs</option>
                  <option value="delivery">3. Delivery & Fulfilment Evidence</option>
                  <option value="merchant">4. Merchant Records & Policies</option>
                </select>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label
                  className="font-mono text-slate-light"
                  style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: '0.06em', textTransform: 'uppercase' }}
                >
                  Evidence Type Slug
                </label>
                <input
                  type="text"
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value)}
                  placeholder="e.g. proof_of_delivery, chat_log, invoice"
                  required
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    background: 'var(--color-ink-mid)',
                    border: '1px solid var(--color-ink-border)',
                    borderRadius: 7,
                    color: 'var(--color-white)',
                    fontSize: 13,
                    boxSizing: 'border-box' as const,
                    fontFamily: 'var(--font-body)',
                  }}
                />
              </div>

              <div style={{ marginBottom: 16 }}>
                <label
                  className="font-mono text-slate-light"
                  style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: '0.06em', textTransform: 'uppercase' }}
                >
                  Attach File (Stored in PostgreSQL)
                </label>
                <input
                  type="file"
                  onChange={handleFileChange}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    background: 'var(--color-ink-mid)',
                    border: '1px solid var(--color-ink-border)',
                    borderRadius: 7,
                    color: 'var(--color-slate-light)',
                    fontSize: 12,
                    boxSizing: 'border-box' as const,
                  }}
                />
              </div>

              <div style={{ marginBottom: 20 }}>
                <label
                  className="font-mono text-slate-light"
                  style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: '0.06em', textTransform: 'uppercase' }}
                >
                  Description / Context
                </label>
                <textarea
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  placeholder="Describe what this document proves..."
                  rows={2}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    background: 'var(--color-ink-mid)',
                    border: '1px solid var(--color-ink-border)',
                    borderRadius: 7,
                    color: 'var(--color-white)',
                    fontSize: 13,
                    boxSizing: 'border-box' as const,
                    fontFamily: 'var(--font-body)',
                    resize: 'vertical' as const,
                  }}
                />
              </div>

              {uploadError && (
                <div className="font-body text-red" style={{ fontSize: 12, marginBottom: 14, color: 'var(--color-red)' }}>
                  {uploadError}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(false)}
                  style={{
                    background: 'var(--color-ink-mid)',
                    border: '1px solid var(--color-ink-border)',
                    color: 'var(--color-slate-light)',
                    padding: '9px 18px',
                    borderRadius: 7,
                    cursor: 'pointer',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    fontWeight: 600,
                    transition: 'background 0.15s ease, color 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = '#1E2D45'
                    ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-white)'
                  }}
                  onMouseLeave={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-ink-mid)'
                    ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--color-slate-light)'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  style={{
                    background: 'var(--color-teal)',
                    color: '#0B1120',
                    border: 'none',
                    padding: '9px 20px',
                    borderRadius: 7,
                    cursor: 'pointer',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    fontWeight: 700,
                    letterSpacing: '0.04em',
                    boxShadow: '0 2px 8px rgba(54,198,174,0.3)',
                    transition: 'background 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal-dim)'
                  }}
                  onMouseLeave={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--color-teal)'
                  }}
                >
                  {uploading ? 'Uploading...' : 'Save & Attach Evidence'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  )
}
