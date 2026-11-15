import { useState } from 'react'
import type { Evidence } from '../types'
import { formatDate } from '../utils'

interface Props {
  evidenceList: Evidence[]
  audit?: any[]
  onUploadClick?: () => void
}

const CATEGORY_CONFIG: Record<string, { label: string; icon: string; description: string; color: string }> = {
  transaction: {
    label: 'TRANSACTION EVIDENCE',
    icon: '💳',
    description: 'Payment gateway captures, amounts, timestamps, and refund records.',
    color: 'var(--color-teal)',
  },
  customer: {
    label: 'CUSTOMER EVIDENCE',
    icon: '👤',
    description: 'Customer communications, support transcripts, and authentication/OTP logs.',
    color: 'var(--color-amber)',
  },
  delivery: {
    label: 'DELIVERY / FULFILMENT EVIDENCE',
    icon: '📦',
    description: 'Carrier tracking, proof of delivery, signatures, and fulfilment records.',
    color: '#4DA8DA',
  },
  merchant: {
    label: 'MERCHANT EVIDENCE',
    icon: '🏢',
    description: 'Refund policy terms, merchant notes, receipts, and order invoices.',
    color: 'var(--color-slate-light)',
  },
}

function mapTypeToCategory(typeStr?: string | null): string {
  if (!typeStr) return 'merchant'
  const t = typeStr.toLowerCase()
  if (['payment', 'refund', 'gateway', 'charge', 'transaction'].includes(t)) return 'transaction'
  if (['communication', 'customer', 'otp', 'auth', 'authentication'].includes(t)) return 'customer'
  if (['delivery', 'tracking', 'fulfillment', 'fulfilment', 'shipping', 'proof_of_receipt'].includes(t)) return 'delivery'
  if (['merchant', 'merchant_communication', 'policy', 'refund_policy', 'invoice', 'receipt', 'merchant_notes'].includes(t)) return 'merchant'
  return 'merchant'
}

export default function EvidencePanel({ evidenceList, onUploadClick }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const grouped: Record<string, Evidence[]> = {
    transaction: [],
    customer: [],
    delivery: [],
    merchant: [],
  }

  for (const ev of evidenceList) {
    const cat = ev.category?.toLowerCase() || mapTypeToCategory(ev.evidence_type)
    if (grouped[cat]) {
      grouped[cat].push(ev)
    } else {
      grouped.merchant.push(ev)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {Object.entries(CATEGORY_CONFIG).map(([catKey, config]) => {
        const items = grouped[catKey] || []
        const hasItems = items.length > 0

        return (
          <div key={catKey} className="card" style={{ overflow: 'hidden' }}>
            <div
              style={{
                padding: '14px 20px',
                background: `color-mix(in srgb, ${config.color} 10%, transparent)`,
                borderBottom: '1px solid var(--color-ink-border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <h3
                  className="font-mono"
                  style={{
                    margin: 0,
                    fontSize: 13,
                    color: config.color,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    letterSpacing: '0.04em',
                  }}
                >
                  <span>{config.icon}</span> {config.label} ({items.length})
                </h3>
                <p className="font-body" style={{ margin: '4px 0 0 0', fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>
                  {config.description}
                </p>
              </div>
              <span
                className="font-mono"
                style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  borderRadius: 3,
                  background: hasItems ? 'rgba(63, 167, 150, 0.2)' : 'rgba(91, 107, 124, 0.2)',
                  color: hasItems ? 'var(--color-teal)' : 'var(--color-slate)',
                }}
              >
                {hasItems ? 'AVAILABLE' : 'MISSING'}
              </span>
            </div>

            <div style={{ padding: '0 20px' }}>
              {items.length === 0 ? (
                <div style={{ padding: '20px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <p className="font-body text-slate" style={{ fontStyle: 'italic', fontSize: 13, margin: 0 }}>
                    No {config.label.toLowerCase()} uploaded or collected.
                  </p>
                  {onUploadClick && (
                    <button
                      type="button"
                      onClick={onUploadClick}
                      style={{
                        background: 'transparent',
                        border: '1px solid var(--color-ink-border)',
                        color: 'var(--color-slate-light)',
                        padding: '4px 10px',
                        borderRadius: 4,
                        fontSize: 11,
                        fontFamily: 'var(--font-mono)',
                        cursor: 'pointer',
                      }}
                    >
                      + Add Evidence
                    </button>
                  )}
                </div>
              ) : (
                items.map(e => (
                  <EvidenceItem
                    key={e.id}
                    e={e}
                    isExpanded={expandedId === e.id}
                    onToggle={() => setExpandedId(expandedId === e.id ? null : e.id)}
                  />
                ))
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function EvidenceItem({
  e,
  isExpanded,
  onToggle,
}: {
  e: Evidence
  isExpanded: boolean
  onToggle: () => void
}) {
  const isDemo = e.content?.note?.toString().startsWith('[DEMO]')
  const verification = (e.verification_status || 'unverified').toUpperCase()
  const verificationColor =
    verification === 'VERIFIED'
      ? 'var(--color-teal)'
      : verification === 'CONTRADICTED'
        ? 'var(--color-red)'
        : 'var(--color-slate)'

  return (
    <div style={{ padding: '16px 0', borderBottom: '1px solid var(--color-ink-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="font-mono" style={{ fontSize: 13, color: 'var(--color-white)', fontWeight: 600 }}>
            {e.filename || e.evidence_type.replace(/_/g, ' ').toUpperCase()}
          </span>
          <span
            className="badge"
            style={{
              background: `color-mix(in srgb, ${verificationColor} 15%, transparent)`,
              color: verificationColor,
              border: `1px solid ${verificationColor}`,
              fontSize: 10,
              padding: '1px 6px',
            }}
          >
            {verification}
          </span>
          {isDemo && (
            <span
              className="badge"
              style={{
                background: 'var(--color-ink-light)',
                color: 'var(--color-slate-light)',
                border: '1px solid var(--color-ink-border)',
                fontSize: 10,
              }}
            >
              DEMO
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="font-mono text-slate" style={{ fontSize: 11 }}>
            {formatDate(e.collected_at)}
          </span>
          <button
            type="button"
            onClick={onToggle}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--color-teal)',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            {isExpanded ? 'Hide Details' : 'View Content'}
          </button>
        </div>
      </div>

      {e.description && (
        <p className="font-body text-slate-light" style={{ fontSize: 13, margin: '0 0 10px 0' }}>
          {e.description}
        </p>
      )}

      {isExpanded && (
        <div
          style={{
            marginTop: 10,
            padding: 12,
            background: 'var(--color-ink-dark)',
            borderRadius: 4,
            border: '1px solid var(--color-ink-border)',
          }}
        >
          <pre
            className="font-mono"
            style={{
              margin: 0,
              fontSize: 11,
              color: 'var(--color-slate-light)',
              overflowX: 'auto',
              maxHeight: 220,
            }}
          >
            {JSON.stringify(e.content, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
