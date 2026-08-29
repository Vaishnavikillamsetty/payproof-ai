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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
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
          padding: '12px 16px',
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
        <span className="font-body" style={{ fontSize: 14 }}>{claim.claim_text}</span>
        <span className="font-mono" style={{ fontSize: 12, color: 'var(--color-slate-light)', textAlign: 'right' }}>{pct}</span>
        <span className="badge" style={{ background: `color-mix(in srgb, ${color} 15%, transparent)`, color: color, justifyContent: 'center' }}>
          {claim.verdict || 'PENDING'}
        </span>
      </button>
      
      {expanded && (
        <div style={{ padding: '16px', background: 'var(--color-ink-light)' }}>
          {reasoning ? (
            <div style={{ marginBottom: 16 }}>
              <span className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>LLM Reasoning</span>
              <p className="font-body" style={{ fontSize: 14, color: 'rgba(255,255,255,0.85)' }}>{reasoning}</p>
            </div>
          ) : null}
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <span className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Supporting Evidence</span>
              {claim.supporting_evidence_ids?.length > 0 ? (
                <ul style={{ paddingLeft: 16, margin: 0, fontSize: 12, color: 'var(--color-slate-light)' }} className="font-mono">
                  {claim.supporting_evidence_ids.map(id => <li key={id}>{id.slice(0,8)}...</li>)}
                </ul>
              ) : (
                 <span className="font-body text-slate-light" style={{ fontSize: 13, fontStyle: 'italic' }}>None specified</span>
              )}
            </div>
            <div>
              <span className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Contradicting Evidence</span>
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
      )}
    </div>
  )
}
