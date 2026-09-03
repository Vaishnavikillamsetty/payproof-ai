import { useState, useEffect } from 'react'
import { api } from '../api'
import type { CaseDetail as CaseDetailType, AuditEntry } from '../types'
import { statusTheme, getAIRecommendation, aiRecommendationLabel, isWebhookOrigin, isDemoCase } from '../utils'
import EvidencePanel from '../components/EvidencePanel'
import AgentActivity from '../components/AgentActivity'
import ClaimList from '../components/ClaimList'
import HumanReviewModal from '../components/HumanReviewModal'

interface Props {
  caseId: string
  onBack: () => void
}

function shortTxn(id: string) {
  const parts = id.split('_')
  return parts.length > 2 ? parts.slice(0, 3).join('_') : (id.length > 12 ? id.slice(0, 12) + '...' : id)
}

function formatAmount(n: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n)
}

function formatDisputeReason(reason: string) {
  return reason.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function DataSourceBadge({ fromWebhook, isDemo, txn }: { fromWebhook: boolean, isDemo: boolean, txn: string }) {
  if (isDemo && txn.startsWith('DEMO_SCN_')) {
    const parts = txn.split('_')
    const num = parts[2]
    return (
      <div style={{ display: 'flex', gap: 6 }}>
        <span className="badge" style={{ background: 'var(--color-ink-light)', color: 'var(--color-slate-light)', border: '1px solid var(--color-ink-border)' }}>
          DEMO SCENARIO {num} / 15
        </span>
      </div>
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

function AiRecommendationCard({ c, audit }: { c: CaseDetailType, audit: AuditEntry[] }) {
  const aiRec = getAIRecommendation(audit)
  const isPending = c.status === 'new' || c.status === 'investigating'
  const isMock = audit.some(a => a.step === 'mock_investigation_mode')
  const usedFallback = audit.some(a => a.step === 'agent_fallback_used')

  if (isPending) {
    return (
      <div className="card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, border: '1px solid var(--color-ink-border)' }}>
        <div style={{ animation: 'spin 1s linear infinite', color: 'var(--color-slate-light)' }}>?</div>
        <div>
          <div className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)', letterSpacing: '0.05em' }}>AI INVESTIGATION IN PROGRESS...</div>
          <div className="font-body text-slate" style={{ fontSize: 13, marginTop: 4 }}>Collecting evidence and verifying claims.</div>
        </div>
      </div>
    )
  }

  const recStr = aiRec?.recommended_action || c.status
  const recColor = (recStr === 'contest' || recStr === 'strong_case') ? 'var(--color-teal)' :
                   (recStr === 'request_more_evidence' || recStr === 'weak_case') ? 'var(--color-amber)' :
                   (recStr === 'escalate' || recStr === 'human_review') ? 'var(--color-red)' : 'var(--color-slate)'

  const recLabel = aiRecommendationLabel(recStr)

  let modeLabel = '?? AI AGENT INVESTIGATION'
  if (isMock) modeLabel = 'DEMO RULE-BASED INVESTIGATION'
  else if (usedFallback) modeLabel = '? DETERMINISTIC FALLBACK'

  return (
    <div className="card" style={{ padding: '24px', marginBottom: 24, borderTop: `4px solid ${recColor}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.1em', marginBottom: 8 }}>
            {modeLabel}
          </div>
          <div className="font-mono" style={{ fontSize: 24, color: recColor, fontWeight: 700, letterSpacing: '0.02em' }}>
            {recLabel}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', marginBottom: 4 }}>CONFIDENCE</div>
          <div className="font-mono" style={{ fontSize: 20, color: 'var(--color-white)' }}>
            {aiRec?.confidence != null ? `${Math.round(aiRec.confidence * 100)}%` : (c.overall_confidence ? `${Math.round(c.overall_confidence * 100)}%` : '---')}
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--color-ink-border)' }}>
        <div className="font-mono text-slate" style={{ fontSize: 11, marginBottom: 8 }}>BASED ON:</div>
        <ul className="font-body" style={{ margin: 0, paddingLeft: 20, color: 'var(--color-slate-light)', fontSize: 13, lineHeight: 1.6 }}>
          <li><span style={{ color: 'var(--color-teal)' }}>?</span> Verified payment evidence</li>
          <li><span style={{ color: 'var(--color-amber)' }}>?</span> Merchant records</li>
          <li>?? AI consistency analysis</li>
        </ul>
        <p className="font-body text-slate" style={{ fontSize: 12, marginTop: 12, fontStyle: 'italic' }}>
          Recommendation only - final action requires human review.
        </p>
      </div>
    </div>
  )
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
  const [reviewOpen, setReviewOpen] = useState(false)

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
        .catch((err: Error) => {
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
        <div style={{ animation: 'spin 1s linear infinite', display: 'inline-block', marginBottom: 16 }}>?</div>
        <div className="font-body text-slate">Loading case details.</div>
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
  
  const needsHuman = ['human_review', 'escalate', 'request_more_evidence', 'strong_case', 'contest', 'accept', 'weak_case'].includes(c.status)
  const contradicted = c.claims.filter(claim => claim.verdict === 'contradicted')

  return (
    <main style={{ maxWidth: 800, margin: '0 auto', padding: '32px 24px' }}>
      
      {/* 1. CASE HEADER */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 36, flexWrap: 'wrap' }}>
        <button
          onClick={onBack}
          style={{
            background: 'var(--color-ink-light)', border: '1px solid var(--color-ink-border)',
            padding: '8px 16px', borderRadius: 4, color: 'var(--color-slate)',
            cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 12,
          }}
        >
          BACK
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
            <span style={{ color: 'var(--color-white)', fontWeight: 500 }}>{formatAmount(c.amount)}</span> . {formatDisputeReason(c.dispute_reason)} . Merchant <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{c.merchant_id.toUpperCase()}</span>
          </div>
          <div className="font-body text-slate-light" style={{ fontSize: 14, fontStyle: 'italic' }}>
            "{c.customer_claim}"
          </div>
        </div>
      </div>

      {/* 2. AI RECOMMENDATION */}
      <AiRecommendationCard c={c} audit={audit} />

      {/* 3. HUMAN REVIEW CTA */}
      {needsHuman && (
        <div style={{ marginBottom: 32 }}>
          <button
            type="button"
            onClick={() => setReviewOpen(true)}
            style={{
              padding: '12px 24px', borderRadius: 6, border: '1px solid var(--color-teal)',
              background: 'rgba(63, 167, 150, 0.1)', color: 'var(--color-teal)',
              fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, letterSpacing: '0.06em',
              cursor: 'pointer', textTransform: 'uppercase', width: '100%'
            }}
          >
            Review AI Recommendation
          </button>
        </div>
      )}
      
      <HumanReviewModal 
        c={c} 
        audit={audit} 
        isOpen={reviewOpen} 
        onClose={() => setReviewOpen(false)} 
        onSuccess={(updated) => setData({ case: updated, audit: data.audit })} 
      />

      {/* 4. AI INVESTIGATION ACTIVITY */}
      <SectionHeader>AI Investigation Pipeline</SectionHeader>
      <AgentActivity audit={audit} />

      {/* 5. EVIDENCE BY SOURCE */}
      <SectionHeader>Evidence by Source</SectionHeader>
      <EvidencePanel evidenceList={c.evidence} />

      {/* 6. CLAIM VERIFICATION */}
      <SectionHeader>Claim Verification</SectionHeader>
      <ClaimList claims={c.claims} audit={audit} />

      {/* 7. CONTRADICTIONS - only shown when contradictions exist */}
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

      {/* 8. MISSING INFORMATION - only shown when relevant */}
      {(c.status === 'request_more_evidence' || c.status === 'weak_case') && (
        <>
          <SectionHeader>Missing Information</SectionHeader>
          <div className="card" style={{ padding: '14px 18px', borderLeft: '4px solid var(--color-amber)' }}>
            <p className="font-body text-slate" style={{ fontSize: 13, margin: '0 0 10px 0', lineHeight: 1.5 }}>
              Insufficient evidence to make a high-confidence recommendation. The following may be needed:
            </p>
            <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--color-slate-light)', fontSize: 13 }}>
              {!c.evidence.some(e => e.evidence_type === 'delivery') && <li>Delivery confirmation or tracking number</li>}
              {!c.evidence.some(e => e.evidence_type === 'communication') && <li>Customer communication logs</li>}
              {!c.evidence.some(e => e.evidence_type === 'otp') && <li>Authentication or OTP verification logs</li>}
            </ul>
          </div>
        </>
      )}

    </main>
  )
}
