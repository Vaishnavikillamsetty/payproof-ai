import type { Evidence } from '../types'
import { formatDate } from '../utils'

interface Props {
  evidenceList: Evidence[]
}

export default function EvidencePanel({ evidenceList }: Props) {
  const verified = evidenceList.filter(e => e.evidence_type === 'payment' || e.evidence_type === 'refund')
  const merchant = evidenceList.filter(e => !['payment', 'refund', 'ai_analysis', 'contradiction', 'risk'].includes(e.evidence_type))
  const aiAnalysis = evidenceList.filter(e => ['ai_analysis', 'contradiction', 'risk'].includes(e.evidence_type))

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

      {/* AI ANALYSIS */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', background: 'rgba(91, 107, 124, 0.1)', borderBottom: '1px solid rgba(91, 107, 124, 0.2)' }}>
          <h3 className="font-mono" style={{ margin: 0, fontSize: 13, color: 'var(--color-slate-light)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>🤖</span> AI ANALYSIS
          </h3>
          <p className="font-body" style={{ margin: '4px 0 0 0', fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>
            System-generated findings and risk assessments.
          </p>
        </div>
        <div style={{ padding: '0 20px' }}>
          {aiAnalysis.length === 0 ? (
            <p className="font-body text-slate" style={{ fontStyle: 'italic', fontSize: 13, margin: '20px 0' }}>No AI records generated for this case.</p>
          ) : (
            aiAnalysis.map(e => <EvidenceItem key={e.id} e={e} />)
          )}
        </div>
      </div>
    </div>
  )
}

function EvidenceItem({ e }: { e: Evidence }) {
  const isDemo = e.content?.note?.toString().startsWith('[DEMO]')
  const skip = new Set(['note'])
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
              {typeof val === 'boolean' ? (val ? 'Yes' : 'No') : String(val ?? '—')}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
