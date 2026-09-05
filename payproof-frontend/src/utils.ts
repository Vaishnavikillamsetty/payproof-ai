import type { CaseStatus, AuditEntry } from './types'

/** Map a case status to its verdict CSS classes for edge, badge, etc. */
export function statusTheme(status: CaseStatus | string | null | undefined) {
  switch (status) {
    case 'strong_case':
    case 'contest':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Contest', dot: '#3FA796' }
    case 'accept':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Accept', dot: '#3FA796' }
    case 'weak_case':
    case 'request_more_evidence':
    case 'evidence_requested':
      return { edgeClass: 'verdict-edge-amber', badgeClass: 'badge-amber', label: 'Evidence Requested', dot: '#E0A339' }
    case 'human_review':
    case 'escalate':
    case 'escalated':
      return { edgeClass: 'verdict-edge-red', badgeClass: 'badge-red', label: 'Escalated', dot: '#D6483C' }
    case 'investigating':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Investigating…', dot: '#5B6B7C' }
    case 'pending_review':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Pending Review', dot: '#5B6B7C' }
    case 'new':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'New', dot: '#5B6B7C' }
    case 'action_required':
      return { edgeClass: 'verdict-edge-amber', badgeClass: 'badge-amber', label: 'Action Required', dot: '#E0A339' }
    case 'under_review':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Under Review', dot: '#5B6B7C' }
    case 'won':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Won', dot: '#3FA796' }
    case 'lost':
      return { edgeClass: 'verdict-edge-red', badgeClass: 'badge-red', label: 'Lost', dot: '#D6483C' }
    case 'closed':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Closed', dot: '#5B6B7C' }
    case 'resolved':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Resolved', dot: '#3FA796' }
    default:
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: status ?? 'Unknown', dot: '#5B6B7C' }
  }
}

/** Keep legacy API rows visually consistent while their lifecycle is backfilled. */
export function lifecycleStatus(status: CaseStatus | string, recommendation: string | null, finalAction: string | null): string {
  if (finalAction) return status
  switch (recommendation?.trim().toLowerCase()) {
    case 'escalate': return 'escalated'
    case 'request_more_evidence': return 'evidence_requested'
    default: return 'pending_review'
  }
}

/** Human-readable AI recommendation from a status or audit log */
export function aiRecommendationLabel(status: CaseStatus | string | null | undefined): string {
  switch (status) {
    case 'strong_case':
    case 'contest': return 'CONTEST'
    case 'accept': return 'ACCEPT'
    case 'weak_case':
    case 'request_more_evidence': return 'REQUEST MORE EVIDENCE'
    case 'human_review': return 'HUMAN REVIEW'
    case 'escalate': return 'ESCALATE'
    case 'new': return 'PENDING'
    case 'investigating': return 'INVESTIGATING…'
    default: return status ? status.toUpperCase().replace(/_/g, ' ') : '—'
  }
}

/** Extract the AI final recommendation step from an audit log */
export function getAIRecommendation(audit: AuditEntry[]): {
  recommended_action: string
  confidence: number | null
  evidence_strength: string | null
  used_fallback: boolean
} | null {
  const recStep = audit.find(a => a.step === 'agent_recommendation_created')
  if (!recStep) return null
  return {
    recommended_action: (recStep.detail?.recommended_action as string) ?? '',
    confidence: (recStep.detail?.confidence as number) ?? null,
    evidence_strength: (recStep.detail?.evidence_strength as string) ?? null,
    used_fallback: recStep.detail?.ai_status === 'FALLBACK',
  }
}

/** Extract agent tool call steps from an audit log */
export function getAgentToolCalls(audit: AuditEntry[]): { tool: string; timestamp: string }[] {
  return audit
    .filter(a => a.step === 'agent_tool_called')
    .map(a => ({
      tool: (a.detail?.tool_name as string) ?? (a.detail?.tool as string) ?? 'unknown',
      timestamp: a.timestamp,
    }))
}

/** Classify an evidence_type into data provenance tier */
export function evidenceProvenance(evidenceType: string): 'razorpay' | 'merchant' | 'ai' {
  const t = evidenceType.toLowerCase()
  if (t.includes('payment') || t.includes('refund') || t.includes('razorpay')) return 'razorpay'
  if (t.includes('ai') || t.includes('analysis') || t.includes('finding')) return 'ai'
  return 'merchant'  // delivery, otp, communication, etc.
}

/** Check if a case originated from a webhook */
export function isWebhookOrigin(audit: AuditEntry[]): boolean {
  return audit.some(a => a.step === 'webhook_case_created')
}

/** Check if case is demo data */
export function isDemoCase(transactionId: string): boolean {
  return transactionId.startsWith('DEMO_TXN_')
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

/** Format a number as currency based on the provided code. */
export function formatAmount(n: number, currency?: string | null): string {
  const displayCurrency = currency?.trim().toUpperCase()
  if (!displayCurrency || displayCurrency === 'UNKNOWN') return `${n.toFixed(2)} UNKNOWN`
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: displayCurrency,
    minimumFractionDigits: 2,
  })
  return `${formatter.format(n)} ${displayCurrency}`
}

/**
 * Return full transaction ID if <=22 chars, otherwise keep prefix + last 4 chars.
 * Preserves DEMO_TXN_STRONG_1 intact (17 chars).
 */
export function shortTxn(txn: string): string {
  if (txn.length <= 22) return txn.toUpperCase()
  return `${txn.slice(0, 14).toUpperCase()}…${txn.slice(-4).toUpperCase()}`
}
