import { useEffect, useState } from 'react'
import { api } from '../api'
import type { CaseDetail as CaseDetailType, AuditEntry, Claim } from '../types'
import EvidencePanel from '../components/EvidencePanel'
import ClaimList from '../components/ClaimList'
import AgentActivity from '../components/AgentActivity'
import CompletenessBar from '../components/CompletenessBar'
import { formatAmount, formatDisputeReason, shortTxn, aiRecommendationLabel, getAIRecommendation, isDemoCase, isWebhookOrigin, statusTheme } from '../utils'

interface Props {
  caseId: string
  onBack: () => void
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

function DataSourceBadge({ fromWebhook, isDemo }: { fromWebhook: boolean; isDemo: boolean }) {
  if (fromWebhook) {
    return (
      <span className="font-mono" style={{
        fontSize: 10, padding: '3px 8px', borderRadius: 3, letterSpacing: '0.08em',
        background: 'rgba(63,167,150,0.15)', color: 'var(--color-teal)', border: '1px solid rgba(63,167,150,0.3)',
      }}>
        ⬡ RAZORPAY WEBHOOK
      </span>
    )
  }
  if (isDemo) {
    return (
      <span className="font-mono" style={{
        fontSize: 10, padding: '3px 8px', borderRadius: 3, letterSpacing: '0.08em',
        background: 'rgba(91,107,124,0.2)', color: 'var(--color-slate-light)', border: '1px solid var(--color-ink-border)',
      }}>
        ⚗ DEMO DATA
      </span>
    )
  }
  return (
    <span className="font-mono" style={{
      fontSize: 10, padding: '3px 8px', borderRadius: 3, letterSpacing: '0.08em',
      background: 'rgba(91,107,124,0.1)', color: 'var(--color-slate)', border: '1px solid var(--color-ink-border)',
    }}>
      MANUAL SUBMISSION
    </span>
  )
}

function AiRecommendationCard({ c, audit }: { c: CaseDetailType; audit: AuditEntry[] }) {
  const aiRec = getAIRecommendation(audit)
  const rec = aiRecommendationLabel(c.status)
  const recColor = REC_COLORS[rec] ?? 'var(--color-slate)'
  const isProcessing = c.status === 'new' || c.status === 'investigating'

  if (isProcessing) {
    return (
      <div className="card" style={{ padding: '20px 24px', borderLeft: '4px solid var(--color-slate)', marginBottom: 24 }}>
        <div className="font-mono text-slate" style={{ fontSize: 10, letterSpacing: '0.1em', marginBottom: 8 }}>🤖 AI INVESTIGATION RESULT</div>
        <div className="font-body text-slate" style={{ fontSize: 14, fontStyle: 'italic' }}>
          Investigation in progress… This page will refresh automatically.
        </div>
      </div>
    )
  }

  return (
    <div className="card" style={{ padding: '20px 24px', borderLeft: `4px solid ${recColor}`, marginBottom: 24 }}>
      <div className="font-mono text-slate" style={{ fontSize: 10, letterSpacing: '0.1em', marginBottom: 12 }}>🤖 AI INVESTIGATION RESULT</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20, marginBottom: 16 }}>
        <div>
          <span className="font-mono text-slate" style={{ fontSize: 10, display: 'block', marginBottom: 4 }}>Recommendation</span>
          <span className="font-mono" style={{ fontSize: 15, fontWeight: 700, color: recColor }}>{rec}</span>
        </div>
        <div>
          <span className="font-mono text-slate" style={{ fontSize: 10, display: 'block', marginBottom: 4 }}>Confidence</span>
          <span className="font-mono" style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-white)' }}>
            {aiRec?.confidence !== null && aiRec?.confidence !== undefined
              ? `${Math.round(aiRec.confidence * 100)}%`
              : c.overall_confidence !== null ? `${Math.round((c.overall_confidence ?? 0) * 100)}%` : '—'}
          </span>
        </div>
        <div>
          <span className="font-mono text-slate" style={{ fontSize: 10, display: 'block', marginBottom: 4 }}>Evidence Strength</span>
          <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>
            {aiRec?.evidence_strength ? aiRec.evidence_strength.toUpperCase() : c.completeness_score !== null ? `${Math.round((c.completeness_score ?? 0) * 100)}%` : '—'}
          </span>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingTop: 12, borderTop: '1px solid var(--color-ink-border)' }}>
        <span className="font-mono text-slate" style={{ fontSize: 10 }}>AI Status:</span>
        {aiRec?.used_fallback ? (
          <span className="font-mono" style={{ fontSize: 11, color: 'var(--color-amber)' }}>DETERMINISTIC FALLBACK — AI model unavailable, rule-based decision used</span>
        ) : (
          <span className="font-mono" style={{ fontSize: 11, color: 'var(--color-teal)' }}>COMPLETED — AI agent executed tool-calling investigation</span>
        )}
      </div>
    </div>
  )
}

function ContradictionsPanel({ claims }: { claims: Claim[] }) {
  const contradicted = claims.filter(c => c.verdict === 'contradicted')
  if (contradicted.length === 0) {
    return (
      <div className="card" style={{ padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <span style={{ color: 'var(--color-teal)' }}>✓</span>
        <span className="font-body text-slate" style={{ fontSize: 13 }}>No contradictions detected.</span>
      </div>
    )
  }
  return (
    <div style={{ marginBottom: 16 }}>
      {contradicted.map(claim => (
        <div key={claim.id} style={{
          background: 'rgba(214,72,60,0.08)', borderLeft: '4px solid var(--color-red)',
          padding: '16px 20px', borderRadius: '0 6px 6px 0', marginBottom: 10,
        }}>
          <div className="font-mono" style={{ color: 'var(--color-red)', fontSize: 11, letterSpacing: '0.08em', marginBottom: 8 }}>
            ⚠ CONTRADICTION DETECTED
          </div>
          <p className="font-body text-white" style={{ fontSize: 14, margin: 0, lineHeight: 1.6 }}>
            {claim.claim_text}
          </p>
          <div className="font-body text-slate" style={{ fontSize: 12, marginTop: 8 }}>
            Conflicting evidence found — this case requires human review. The system will not auto-resolve a contradiction.
          </div>
        </div>
      ))}
    </div>
  )
}

function HumanReviewCTA({ status }: { status: string }) {
  const needsHuman = ['human_review', 'escalate', 'request_more_evidence', 'strong_case', 'contest', 'accept'].includes(status)
  if (!needsHuman) return null

  return (
    <div style={{
      background: 'rgba(224,163,57,0.08)', border: '1px solid rgba(224,163,57,0.3)',
      borderRadius: 8, padding: '20px 24px', marginBottom: 24,
    }}>
      <div className="font-mono" style={{ color: 'var(--color-amber)', fontSize: 11, letterSpacing: '0.1em', marginBottom: 12 }}>
        ⚡ HUMAN REVIEW REQUIRED
      </div>
      <p className="font-body text-white" style={{ fontSize: 14, lineHeight: 1.6, margin: '0 0 16px 0' }}>
        The AI system has produced a recommendation but <strong>will not automatically accept or contest this dispute</strong>.
        A human agent must review the evidence and make the final decision.
      </p>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <button
          type="button"
          style={{
            padding: '8px 18px', borderRadius: 5, border: '1px solid var(--color-amber)',
            background: 'rgba(224,163,57,0.1)', color: 'var(--color-amber)',
            fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, letterSpacing: '0.06em',
            cursor: 'pointer', textTransform: 'uppercase',
          }}
          onClick={() => alert('Evidence review workflow — connect to dispute management system to take action.')}
        >
          Review Evidence
        </button>
        <button
          type="button"
          style={{
            padding: '8px 18px', borderRadius: 5, border: '1px solid var(--color-ink-border)',
            background: 'transparent', color: 'var(--color-slate)',
            fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, letterSpacing: '0.06em',
            cursor: 'pointer', textTransform: 'uppercase',
          }}
          onClick={() => alert('Escalation workflow — connect to dispute management system to escalate.')}
        >
          Mark for Escalation
        </button>
      </div>
      <p className="font-mono text-slate" style={{ fontSize: 10, marginTop: 12, marginBottom: 0, letterSpacing: '0.04em' }}>
        NOTE: Razorpay Accept/Contest API actions are not automated by this system. All financial decisions require explicit human authorisation.
      </p>
    </div>
  )
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-mono text-slate" style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 16, marginTop: 0 }}>
      {children}
    </h2>
  )
}

export default function CaseDetail({ caseId, onBack }: Props) {
  const [data, setData] = useState<{ case: CaseDetailType; audit: AuditEntry[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    let pollInterval: number | undefined

    const load = () => {
      Promise.all([api.getCase(caseId), api.getAudit(caseId)])
        .then(([c, a]) => {
          if (!isMounted) return
          setData({ case: c, audit: a })
          setError(null)
          setLoading(false)

          if (c.status === 'new' || c.status === 'investigating') {
            if (!pollInterval) pollInterval = window.setInterval(load, 3000)
          } else {
            if (pollInterval) { clearInterval(pollInterval); pollInterval = undefined }
          }
        })
        .catch((err) => {
          if (!isMounted) return
          setError(err.message)
          setLoading(false)
        })
    }

    setLoading(true)
    load()
    return () => {
      isMounted = false
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [caseId])

  if (loading && !data) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-slate)' }}>
        <div style={{ animation: 'spin 1s linear infinite', display: 'inline-block', marginBottom: 16 }}>◒</div>
        <div className="font-body text-slate">Loading case details…</div>
      </div>
    )
  }
  if (error || !data) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-red)' }}>
        <div className="font-mono">ERROR</div>
        <div className="font-body">{error}</div>
        <button onClick={onBack} style={{ marginTop: 16, cursor: 'pointer', background: 'transparent', border: '1px solid var(--color-red)', color: 'var(--color-red)', padding: '4px 12px', borderRadius: 4 }}>Go Back</button>
      </div>
    )
  }

  const c = data.case
  const audit = data.audit
  const fromWebhook = isWebhookOrigin(audit)
  const demo = isDemoCase(c.transaction_id)
  const theme = statusTheme(c.status)

  return (
    <main style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
      {/* ── A. CASE HEADER ──────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 36, flexWrap: 'wrap' }}>
        <button
          onClick={onBack}
          style={{
            background: 'var(--color-ink-light)', border: '1px solid var(--color-ink-border)',
            padding: '8px 16px', borderRadius: 4, color: 'var(--color-slate)',
            cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 12,
          }}
        >
          ← BACK
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
            <h1 className="font-mono" style={{ fontSize: 22, margin: 0, color: 'var(--color-white)', letterSpacing: '0.05em' }}>
              {shortTxn(c.transaction_id)}
            </h1>
            <DataSourceBadge fromWebhook={fromWebhook} isDemo={demo} />
            <span className="font-mono" style={{
              fontSize: 10, padding: '3px 8px', borderRadius: 3, letterSpacing: '0.08em',
              background: `color-mix(in srgb, ${theme.dot} 15%, transparent)`, color: theme.dot,
            }}>
              {theme.label}
            </span>
          </div>
          <div className="font-body text-slate" style={{ fontSize: 14 }}>
            {formatDisputeReason(c.dispute_reason)} ·{' '}
            <span style={{ color: 'var(--color-white)', fontWeight: 500 }}>{formatAmount(c.amount)}</span> ·{' '}
            Merchant <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{c.merchant_id.toUpperCase()}</span>
          </div>
          <div className="font-body text-slate" style={{ fontSize: 12, marginTop: 4 }}>
            {c.customer_claim}
          </div>
        </div>
      </div>

      {/* ── B. AI RECOMMENDATION ────────────────────────────── */}
      <SectionHeader>AI Investigation Result</SectionHeader>
      <AiRecommendationCard c={c} audit={audit} />

      {/* ── Human Review CTA ───────────────────────────────── */}
      <HumanReviewCTA status={c.status} />

      {/* ── Two-column layout ──────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48 }}>

        {/* LEFT: Evidence ──────────────────────────────────── */}
        <div>
          <SectionHeader>Evidence</SectionHeader>
          <EvidencePanel evidenceList={c.evidence} />

          {/* Missing Evidence (if requesting more) */}
          {(c.status === 'request_more_evidence' || c.status === 'weak_case') && (
            <div style={{ marginTop: 24 }}>
              <SectionHeader>⚠ Missing Information</SectionHeader>
              <div className="card" style={{ padding: '14px 18px', borderLeft: '4px solid var(--color-amber)' }}>
                <p className="font-body text-slate" style={{ fontSize: 13, margin: '0 0 10px 0', lineHeight: 1.5 }}>
                  Insufficient evidence to make a high-confidence recommendation. The following may be needed:
                </p>
                <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--color-slate-light)' }}>
                  {!c.evidence_types?.includes('delivery') && <li className="font-body" style={{ fontSize: 13, marginBottom: 4 }}>Delivery confirmation / tracking record</li>}
                  {!c.evidence_types?.includes('otp_log') && <li className="font-body" style={{ fontSize: 13, marginBottom: 4 }}>OTP / authentication verification</li>}
                  {!c.evidence_types?.includes('communication') && <li className="font-body" style={{ fontSize: 13, marginBottom: 4 }}>Customer communication record</li>}
                  {!c.evidence_types?.includes('payment_gateway') && <li className="font-body" style={{ fontSize: 13 }}>Payment gateway confirmation</li>}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Analysis ──────────────────────────────────── */}
        <div>
          {/* Contradictions */}
          <SectionHeader>Contradictions</SectionHeader>
          <ContradictionsPanel claims={c.claims} />

          {/* Evidence completeness */}
          <SectionHeader>Evidence Completeness</SectionHeader>
          <div className="card" style={{ padding: '16px 20px', marginBottom: 24 }}>
            <CompletenessBar score={c.completeness_score} showLabel={true} showChecklist={true} evidence={c.evidence} />
          </div>

          {/* Agent Activity */}
          <SectionHeader>Agent Activity</SectionHeader>
          <AgentActivity audit={audit} />

          {/* Per-claim verification */}
          {c.claims.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <SectionHeader>Per-Claim Verification</SectionHeader>
              <ClaimList claims={c.claims} audit={audit} />
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
