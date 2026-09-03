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
  
  // Try to find reasoning from audit log (if real AI was used)
  const auditEntry = audit.find(a => a.step === 'claim_verified' && a.detail?.claim === claim.claim_text)
  const reasoning = auditEntry?.detail?.reasoning as string | undefined

  let color = 'var(--color-slate)'
  if (claim.verdict === 'supported') color = 'var(--color-teal)'
  if (claim.verdict === 'contradicted') color = 'var(--color-red)'
  if (claim.verdict === 'unverifiable') color = 'var(--color-amber)'

  const isMock = audit.some(a => a.step === 'mock_investigation_mode')
  
  let sourceText = '🤖 AI ANALYSIS'
  if (isMock) {
    if (claim.verdict === 'contradicted') sourceText = '◐ MERCHANT EVIDENCE'
    else if (claim.verdict === 'supported') sourceText = '✓ VERIFIED SOURCE'
    else sourceText = '🤖 AI ANALYSIS'
  }

  const verdictLabel = claim.verdict ? claim.verdict.toUpperCase() : 'PENDING'
  let icon = '?'
  if (claim.verdict === 'supported') icon = '✓'
  if (claim.verdict === 'contradicted') icon = '⚠'
  
  const formattedVerdict = claim.verdict ? `${icon} ${verdictLabel}` : 'PENDING'
  const pct = claim.confidence !== null ? `${Math.round(claim.confidence * 100)}%` : '—'

  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      <button 
        type="button" 
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          display: 'grid',
          gridTemplateColumns: '1fr auto',
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em' }}>CUSTOMER CLAIM</span>
          <span className="font-body" style={{ fontSize: 14 }}>"{claim.claim_text}"</span>
        </div>
        <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
           <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em' }}>STATUS</span>
           <span className="badge" style={{ background: `color-mix(in srgb, ${color} 15%, transparent)`, color: color, fontSize: 12, fontWeight: 600 }}>
             {formattedVerdict}
           </span>
        </div>
      </button>
      
      {expanded && (
        <div style={{ padding: '20px', background: 'var(--color-ink-light)', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {claim.verdict === 'contradicted' && (
            <div style={{ padding: '12px 16px', background: 'rgba(214, 72, 60, 0.1)', borderLeft: '3px solid var(--color-red)' }}>
              <div className="font-mono" style={{ color: 'var(--color-red)', fontSize: 11, marginBottom: 4 }}>⚠ HUMAN REVIEW REQUIRED</div>
              <div className="font-body text-white" style={{ fontSize: 13 }}>System detected a contradiction. Auto-resolution disabled.</div>
            </div>
          )}
          
          <div>
            <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', display: 'block', marginBottom: 4 }}>EVIDENCE</span>
            <div className="font-body text-white" style={{ fontSize: 14 }}>
              {reasoning ? reasoning : (
                 claim.verdict === 'contradicted' ? 'Evidence found that directly contradicts the customer claim.' :
                 claim.verdict === 'supported' ? 'Verified evidence supports the customer claim.' :
                 'Insufficient evidence to confidently verify or contradict this claim.'
              )}
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: 32 }}>
            <div>
              <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', display: 'block', marginBottom: 4 }}>SOURCE</span>
              <div className="font-mono text-white" style={{ fontSize: 12 }}>{sourceText}</div>
            </div>
            <div>
              <span className="font-mono text-slate" style={{ fontSize: 11, letterSpacing: '0.05em', display: 'block', marginBottom: 4 }}>CONFIDENCE</span>
              <div className="font-mono text-white" style={{ fontSize: 12 }}>{pct}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
