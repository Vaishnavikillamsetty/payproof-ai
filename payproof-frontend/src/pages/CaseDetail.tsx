import { useEffect, useState } from 'react'
import { api } from '../api'
import type { CaseDetail as CaseDetailType, AuditEntry } from '../types'
import EvidenceTimeline from '../components/EvidenceTimeline'
import ClaimList from '../components/ClaimList'
import VerdictStamp from '../components/VerdictStamp'
import CompletenessBar from '../components/CompletenessBar'
import { formatAmount, formatDisputeReason, shortTxn } from '../utils'

interface Props {
  caseId: string
  onBack: () => void
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

          // Poll if the case is still processing
          if (c.status === 'new' || c.status === 'investigating') {
            if (!pollInterval) {
              pollInterval = window.setInterval(load, 3000)
            }
          } else {
            if (pollInterval) {
              clearInterval(pollInterval)
              pollInterval = undefined
            }
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
        <div className="font-body text-slate">Loading case details...</div>
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
  
  // Find policy decision step for routing reason / draft response logic
  const policyStep = audit.find(a => a.step === 'policy_decision')
  const routingReason = policyStep?.detail?.reason as string | undefined

  return (
    <main style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 40 }}>
        <button 
          onClick={onBack}
          style={{ 
            background: 'var(--color-ink-light)', border: '1px solid var(--color-ink-border)', 
            padding: '8px 16px', borderRadius: 4, color: 'var(--color-slate)', 
            cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 12,
            transition: 'background 0.2s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-ink-border)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--color-ink-light)')}
        >
          ← BACK
        </button>
        <div>
          <h1 className="font-mono" style={{ fontSize: 24, margin: 0, color: 'var(--color-white)' }}>
            {shortTxn(c.transaction_id)}
          </h1>
          <div className="font-body text-slate" style={{ fontSize: 14, marginTop: 4 }}>
            {formatDisputeReason(c.dispute_reason)} · {formatAmount(c.amount)} · Merchant {c.merchant_id.toUpperCase()}
          </div>
        </div>
      </div>
      
      {/* Two-column Layout (Section 8 docs/build-plan.md) */}
      <div style={{ display: 'grid', gridTemplateColumns: '5fr 7fr', gap: 60 }}>
        
        {/* Left Column: Evidence Timeline */}
        <section>
          <h2 className="font-mono text-slate" style={{ fontSize: 14, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 24 }}>
            Evidence Timeline
          </h2>
          <EvidenceTimeline evidenceList={c.evidence} />
        </section>

        {/* Right Column: Reasoning & Decision */}
        <section>
          <div style={{ marginBottom: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <VerdictStamp status={c.status} confidence={c.overall_confidence} size="large" />
            
            {/* Legend / Type System */}
            <div style={{ display: 'flex', gap: 16, background: 'var(--color-ink-light)', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--color-ink-border)' }}>
              <span className="font-body text-slate" style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>🗣️ Claim</span>
              <span className="font-body text-slate" style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>📄 Evidence</span>
              <span className="font-body text-slate" style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>⚙️ Rule</span>
            </div>
          </div>

          {c.status === 'human_review' && (
            <div style={{ background: 'rgba(224, 163, 57, 0.1)', borderLeft: '4px solid var(--color-amber)', padding: '20px 24px', marginBottom: 40, borderRadius: '0 6px 6px 0' }}>
              <h3 className="font-mono" style={{ color: 'var(--color-amber)', fontSize: 14, textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                ⚠️ Human Review Required
              </h3>
              <p className="font-body text-white" style={{ fontSize: 15, margin: 0, lineHeight: 1.5 }}>
                {routingReason || 'The system flagged this case for manual review.'}
              </p>
            </div>
          )}

          <div className="card" style={{ padding: '24px 28px', marginBottom: 40 }}>
             <h3 className="font-mono text-slate" style={{ fontSize: 12, textTransform: 'uppercase', marginBottom: 16 }}>
                Completeness Score
             </h3>
             <CompletenessBar score={c.completeness_score} showLabel={true} showChecklist={true} evidence={c.evidence} />
             
             {routingReason && c.status !== 'human_review' ? (
               <div style={{ marginTop: 28, paddingTop: 24, borderTop: '1px solid var(--color-ink-border)' }}>
                 <h3 className="font-mono text-slate" style={{ fontSize: 12, textTransform: 'uppercase', marginBottom: 12 }}>
                    Policy Gate Decision
                 </h3>
                 <p className="font-body text-white" style={{ fontSize: 15, lineHeight: 1.5 }}>
                   {routingReason}
                 </p>
               </div>
             ) : (!routingReason && (
               <div style={{ marginTop: 28, paddingTop: 24, borderTop: '1px solid var(--color-ink-border)' }}>
                 <p className="font-body text-slate" style={{ fontSize: 14, fontStyle: 'italic' }}>
                   Policy decision is pending processing.
                 </p>
               </div>
             ))}
          </div>

          <h2 className="font-mono text-slate" style={{ fontSize: 14, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 20 }}>
            Per-Claim Verification
          </h2>
          {c.claims.length > 0 ? (
            <ClaimList claims={c.claims} audit={audit} />
          ) : (
            <div className="card" style={{ padding: 24, textAlign: 'center' }}>
              <p className="font-body text-slate" style={{ fontSize: 14, fontStyle: 'italic' }}>
                Claims have not been derived yet. Case is awaiting processing.
              </p>
            </div>
          )}
        </section>
      </div>
    </main>
  )
}
