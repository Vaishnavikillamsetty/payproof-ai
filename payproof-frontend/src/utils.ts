import type { CaseStatus } from './types'

/** Map a case status to its verdict CSS classes for edge, badge, etc. */
export function statusTheme(status: CaseStatus | null | undefined) {
  switch (status) {
    case 'strong_case':
      return {
        edgeClass: 'verdict-edge-teal',
        badgeClass: 'badge-teal',
        label: 'Strong Case',
        dot: '#3FA796',
      }
    case 'weak_case':
      return {
        edgeClass: 'verdict-edge-amber',
        badgeClass: 'badge-amber',
        label: 'Weak Case',
        dot: '#E0A339',
      }
    case 'human_review':
      return {
        edgeClass: 'verdict-edge-red',
        badgeClass: 'badge-red',
        label: 'Human Review',
        dot: '#D6483C',
      }
    case 'investigating':
      return {
        edgeClass: 'verdict-edge-slate',
        badgeClass: 'badge-slate',
        label: 'Investigating…',
        dot: '#5B6B7C',
      }
    case 'new':
      return {
        edgeClass: 'verdict-edge-slate',
        badgeClass: 'badge-slate',
        label: 'New',
        dot: '#5B6B7C',
      }
    default:
      return {
        edgeClass: 'verdict-edge-slate',
        badgeClass: 'badge-slate',
        label: status ?? 'Unknown',
        dot: '#5B6B7C',
      }
  }
}

/** Format a dispute_reason slug into a human-readable label. */
export function formatDisputeReason(reason: string): string {
  return reason
    .split(/[_\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

/** Format ISO timestamp to "Aug 30, 2026 · 00:41". */
export function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

/** Format a number as USD. */
export function formatAmount(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(n)
}

/** Truncate a UUID to "TXN_XXXX…XXXX" shortform. */
export function shortTxn(txn: string): string {
  return txn.toUpperCase().slice(0, 16)
}
