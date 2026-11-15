import type { Evidence } from '../types'

interface Props {
  /** 0-100 or computed from categories */
  score: number | null
  /** Show a text label beside the bar */
  showLabel?: boolean
  /** Show the detailed available/missing checklist below the bar */
  showChecklist?: boolean
  /** List of evidence records for the case */
  evidence?: Evidence[]
  /** Explicit list of canonical categories available (transaction, customer, delivery, merchant) */
  categoriesAvailable?: string[]
}

const CANONICAL_CATEGORIES = [
  { id: 'transaction', label: 'Transaction & Payment' },
  { id: 'customer', label: 'Customer & Authentication' },
  { id: 'delivery', label: 'Delivery & Fulfilment' },
  { id: 'merchant', label: 'Merchant Records' },
]

function mapTypeToCategory(typeStr?: string | null): string | null {
  if (!typeStr) return null
  const t = typeStr.toLowerCase()
  if (['payment', 'refund', 'gateway', 'charge', 'transaction'].includes(t)) return 'transaction'
  if (['communication', 'customer', 'otp', 'auth', 'authentication'].includes(t)) return 'customer'
  if (['delivery', 'tracking', 'fulfillment', 'fulfilment', 'shipping', 'proof_of_receipt'].includes(t)) return 'delivery'
  if (['merchant', 'merchant_communication', 'policy', 'refund_policy', 'invoice', 'receipt', 'merchant_notes'].includes(t)) return 'merchant'
  return null
}

export default function CompletenessBar({
  score,
  showLabel = true,
  showChecklist = false,
  evidence = [],
  categoriesAvailable,
}: Props) {
  const availableSet = new Set<string>()
  if (categoriesAvailable && categoriesAvailable.length > 0) {
    categoriesAvailable.forEach(c => availableSet.add(c.toLowerCase()))
  } else {
    for (const e of evidence) {
      const cat = e.category?.toLowerCase() || mapTypeToCategory(e.evidence_type)
      if (cat) availableSet.add(cat)
    }
  }

  const count = availableSet.size
  const effectivePct = score !== null && score !== undefined ? Math.max(0, Math.min(100, score)) : Math.round((count / 4) * 100)
  const color =
    effectivePct >= 75
      ? 'var(--color-teal)'
      : effectivePct >= 50
        ? 'var(--color-amber)'
        : 'var(--color-red)'

  const available = CANONICAL_CATEGORIES.filter(c => availableSet.has(c.id))
  const missing = CANONICAL_CATEGORIES.filter(c => !availableSet.has(c.id))

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <div
          style={{
            flex: 1,
            height: 4,
            borderRadius: 2,
            background: 'var(--color-ink-border)',
            overflow: 'hidden',
          }}
          role="progressbar"
          aria-valuenow={effectivePct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Evidence completeness ${effectivePct}%`}
        >
          <div
            style={{
              width: `${effectivePct}%`,
              height: '100%',
              background: color,
              borderRadius: 2,
              transition: 'width 0.4s ease',
            }}
          />
        </div>
        {showLabel && (
          <span
            className="font-mono"
            style={{ fontSize: 12, color, minWidth: 32, textAlign: 'right' }}
          >
            {count} / 4 categories available
          </span>
        )}
      </div>

      {showChecklist && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          <div>
            <h4 className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', marginBottom: 8 }}>Available</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, gap: 4, display: 'flex', flexDirection: 'column' }}>
              {available.map(item => (
                <li key={item.id} className="font-body text-slate" style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: 'var(--color-teal)' }}>✓</span> {item.label}
                </li>
              ))}
              {available.length === 0 && <li className="font-body text-slate-light" style={{ fontSize: 13, fontStyle: 'italic' }}>None</li>}
            </ul>
          </div>
          <div>
            <h4 className="font-mono text-slate" style={{ fontSize: 11, textTransform: 'uppercase', marginBottom: 8 }}>Missing</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, gap: 4, display: 'flex', flexDirection: 'column' }}>
              {missing.map(item => (
                <li key={item.id} className="font-body text-slate" style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: 'var(--color-red)' }}>✗</span> {item.label}
                </li>
              ))}
              {missing.length === 0 && <li className="font-body text-slate-light" style={{ fontSize: 13, fontStyle: 'italic' }}>None</li>}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
