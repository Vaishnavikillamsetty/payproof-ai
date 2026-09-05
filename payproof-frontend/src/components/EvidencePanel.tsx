import type { Evidence } from '../types'
import { formatAmount, formatDate } from '../utils'

interface Props {
  evidenceList: Evidence[]
  audit?: any[]
}

export default function EvidencePanel({ evidenceList, audit = [] }: Props) {
  const verified = evidenceList.filter(e => e.evidence_type === 'payment' || e.evidence_type === 'refund')
  const merchant = evidenceList.filter(e => !['payment', 'refund', 'ai_analysis', 'contradiction', 'risk'].includes(e.evidence_type))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* VERIFIED SOURCE */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', background: 'rgba(63, 167, 150, 0.1)', borderBottom: '1px solid rgba(63, 167, 150, 0.2)' }}>
          <h3 className="font-mono" style={{ margin: 0, fontSize: 13, color: 'var(--color-teal)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>✓</span> VERIFIED SOURCE
          </h3>
          <p className="font-body" style={{ margin: '4px 0 0 0', fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>
            Immutable records from the payment gateway.
          </p>
        </div>
        <div style={{ padding: '0 20px' }}>
          {verified.length === 0 ? (
            <p className="font-body text-slate" style={{ fontStyle: 'italic', fontSize: 13, margin: '20px 0' }}>No verified records found.</p>
          ) : (
            verified.map(e => <EvidenceItem key={e.id} e={e} />)
          )}
        </div>
      </div>

      {/* MERCHANT EVIDENCE */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', background: 'rgba(224, 163, 57, 0.1)', borderBottom: '1px solid rgba(224, 163, 57, 0.2)' }}>
          <h3 className="font-mono" style={{ margin: 0, fontSize: 13, color: 'var(--color-amber)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>◐</span> MERCHANT EVIDENCE
          </h3>
          <p className="font-body" style={{ margin: '4px 0 0 0', fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>
            Information provided by the merchant (delivery, OTP, comms).
          </p>
        </div>
        <div style={{ padding: '0 20px' }}>
          {merchant.length === 0 ? (
            <p className="font-body text-slate" style={{ fontStyle: 'italic', fontSize: 13, margin: '20px 0' }}>No merchant evidence provided.</p>
          ) : (
            merchant.map(e => <EvidenceItem key={e.id} e={e} />)
          )}
        </div>
      </div>

      {/* SYSTEM/AI ANALYSIS */}
      {(() => {
        const isMock = audit.some(a => a.step === 'mock_investigation_mode')
        const usedFallback = audit.some(a => a.step === 'agent_fallback_used')
        const title = isMock || usedFallback ? "RULE ANALYSIS / SYSTEM ANALYSIS" : "AI ANALYSIS"
        const subtitle = isMock || usedFallback ? "Deterministic safety analysis used because live AI verification is unavailable." : "System-generated findings and risk assessments."
        const recStep = audit.find(a => a.step === 'agent_recommendation_created')

        return (
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', background: 'rgba(91, 107, 124, 0.1)', borderBottom: '1px solid rgba(91, 107, 124, 0.2)' }}>
              <h3 className="font-mono" style={{ margin: 0, fontSize: 13, color: 'var(--color-slate-light)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>🤖</span> {title}
              </h3>
              <p className="font-body" style={{ margin: '4px 0 0 0', fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>
                {subtitle}
              </p>
            </div>
            <div style={{ padding: '20px' }}>
              {!recStep ? (
                <p className="font-body text-slate" style={{ fontStyle: 'italic', fontSize: 13, margin: 0 }}>No analysis records generated yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>Summary</span>
                    <span className="font-body" style={{ fontSize: 14, color: 'var(--color-white)' }}>{String(recStep.detail?.summary || '-')}</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 }}>
                    <div>
                      <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>Recommended Action</span>
                      <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>{String(recStep.detail?.recommended_action || '-').toUpperCase()}</span>
                    </div>
                    <div>
                      <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>Confidence</span>
                      <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>{recStep.detail?.confidence != null ? `${Math.round(Number(recStep.detail.confidence) * 100)}%` : '-'}</span>
                    </div>
                    <div>
                      <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>Risk Level</span>
                      <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>{String(recStep.detail?.risk_level || '-').toUpperCase()}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      })()}
    </div>
  )
}

function EvidenceItem({ e }: { e: Evidence }) {
  const isDemo = e.content?.note?.toString().startsWith('[DEMO]')
  const skip = new Set(['note'])
  if (e.evidence_type === 'payment' && e.content.currency) skip.add('currency')
  const entries = Object.entries(e.content).filter(([k]) => !skip.has(k))

  return (
    <div style={{ padding: '20px 0', borderBottom: '1px solid var(--color-ink-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="font-mono" style={{ fontSize: 14, color: 'var(--color-white)', fontWeight: 600, textTransform: 'uppercase' }}>
            {e.evidence_type.replace(/_/g, ' ')}
          </span>
          {isDemo && (
             <span className="badge" style={{ background: 'var(--color-ink-light)', color: 'var(--color-slate-light)', border: '1px solid var(--color-ink-border)', fontSize: 10 }}>
               DEMO
             </span>
          )}
        </div>
        <span className="font-mono text-slate" style={{ fontSize: 11 }}>
          {formatDate(e.collected_at)}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 }}>
        {entries.map(([key, val]) => (
          <div key={key}>
            <span className="font-mono text-slate" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>
              {key.replace(/_/g, ' ')}
            </span>
            <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)' }}>
              {typeof val === 'boolean'
                ? (val ? 'Yes' : 'No')
                : (e.evidence_type === 'payment' && key === 'amount'
                  ? formatAmount(Number(val), String(e.content.currency ?? ''))
                  : String(val ?? '—'))}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
