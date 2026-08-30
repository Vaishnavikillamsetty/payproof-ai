import { useState } from 'react'
import type { Claim, AuditEntry } from '../types'

interface Props {
  claims: Claim[]
  audit: AuditEntry[]
}

export default function ClaimList({ claims, audit }: Props) {
  if (claims.length === 0) {
    return <div className="font-body text-slate" style={{ fontStyle: 'italic', fontSize: 14 }}>No claims generated.</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {claims.map((c) => (
        <ClaimRow key={c.id} claim={c} audit={audit} />
      ))}
    </div>
  )
}

function ClaimRow({ claim, audit }: { claim: Claim, audit: AuditEntry[] }) {
  const [expanded, setExpanded] = useState(false)
  
  // Extract reasoning from audit log since it's not stored in the claim model directly
  const auditEntry = audit.find(a => a.step === 'claim_verified' && a.detail?.claim === claim.claim_text)
  const reasoning = auditEntry?.detail?.reasoning as string | undefined

  let color = 'var(--color-slate)'
  if (claim.verdict === 'supported') color = 'var(--color-teal)'
  if (claim.verdict === 'contradicted') color = 'var(--color-red)'
  if (claim.verdict === 'unverifiable') color = 'var(--color-amber)'

  const pct = claim.confidence !== null ? `${Math.round(claim.confidence * 100)}%` : '—'

  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      <button 
        type="button" 
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          display: 'grid',
          gridTemplateColumns: '1fr 50px 100px',
          gap: 12,
          padding: '16px 20px',
          alignItems: 'center',
          background: expanded ? 'var(--color-ink)' : 'var(--color-ink-light)',
          border: 'none',
          borderBottom: expanded ? '1px solid var(--color-ink-border)' : 'none',
          cursor: 'pointer',
          textAlign: 'left',
          color: 'var(--color-white)',
          transition: 'background 0.15s ease',
        }}
      >
        <span className="font-body" style={{ fontSize: 14, display: 'flex', gap: 8, alignItems: 'center' }}>
          🗣️ {claim.claim_text}
        </span>
        <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-slate-light)', textAlign: 'right' }}>{pct}</span>
        <span className="badge" style={{ background: `color-mix(in srgb, ${color} 15%, transparent)`, color: color, justifyContent: 'center' }}>
          {claim.verdict || 'PENDING'}
        </span>
      </button>
      
      {expanded && (
        <div style={{ padding: '20px', background: 'var(--color-ink-light)' }}>
          {claim.verdict === 'contradicted' && (
            <div style={{ background: 'rgba(214, 72, 60, 0.1)', borderLeft: '4px solid var(--color-red)', padding: '16px', marginBottom: 24, borderRadius: '0 4px 4px 0' }}>
              <h4 className="font-mono" style={{ color: 'var(--color-red)', fontSize: 13, textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                ⚠️ Contradictory Evidence Detected
              </h4>
              <p className="font-body text-white" style={{ fontSize: 14, margin: '0 0 8px 0', lineHeight: 1.5 }}>
                Human Review Required — the system will not auto-resolve a contradiction.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span className="font-body text-slate-light" style={{ fontSize: 13 }}>🗣️ <strong>Claim:</strong> {claim.claim_text}</span>
                <span className="font-body text-slate-light" style={{ fontSize: 13 }}>📄 <strong>Conflicting Evidence:</strong> {claim.contradicting_evidence_ids?.length ? `${claim.contradicting_evidence_ids.length} record(s)` : 'Found in audit'}</span>
              </div>
            </div>
          )}
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Linear chain: Evidence -> Verdict -> Confidence -> Reason */}
            <div>
              <span className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>📄 Evidence Links</span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <span className="font-body text-slate" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Supporting</span>
                  {claim.supporting_evidence_ids?.length > 0 ? (
                    <ul style={{ paddingLeft: 16, margin: 0, fontSize: 12, color: 'var(--color-slate-light)' }} className="font-mono">
                      {claim.supporting_evidence_ids.map(id => <li key={id}>{id.slice(0,8)}...</li>)}
                    </ul>
                  ) : (
                     <span className="font-body text-slate-light" style={{ fontSize: 13, fontStyle: 'italic' }}>None specified</span>
                  )}
                </div>
                <div>
                  <span className="font-body text-slate" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Contradicting</span>
                  {claim.contradicting_evidence_ids?.length > 0 ? (
                    <ul style={{ paddingLeft: 16, margin: 0, fontSize: 12, color: 'var(--color-slate-light)' }} className="font-mono">
                      {claim.contradicting_evidence_ids.map(id => <li key={id}>{id.slice(0,8)}...</li>)}
                    </ul>
                  ) : (
                     <span className="font-body text-slate-light" style={{ fontSize: 13, fontStyle: 'italic' }}>None specified</span>
                  )}
                </div>
              </div>
            </div>

            <div>
              <span className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>⚙️ LLM Verification</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 12 }}>
                <div>
                  <span className="font-body text-slate" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Verdict</span>
                  <span className="font-mono" style={{ fontSize: 13, color: color, textTransform: 'uppercase' }}>{claim.verdict}</span>
                </div>
                <div>
                  <span className="font-body text-slate" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Confidence</span>
                  <span className="font-mono text-white" style={{ fontSize: 13 }}>{pct}</span>
                </div>
              </div>
              <p className="font-body text-slate-light" style={{ fontSize: 11, fontStyle: 'italic', margin: '0 0 12px 0' }}>
                * Indicates how strongly available evidence supports the claim — not certainty that either party is correct.
              </p>
              
              {reasoning && (
                <div>
                  <span className="font-body text-slate" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Reasoning</span>
                  <p className="font-body" style={{ fontSize: 14, color: 'rgba(255,255,255,0.85)', margin: 0, lineHeight: 1.5 }}>{reasoning}</p>
                </div>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  )
}
