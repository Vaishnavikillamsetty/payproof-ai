import type { CaseStatus, AuditEntry } from './types'

export function statusTheme(status: CaseStatus | string | null | undefined) {
  const norm = (status ?? '').toString().toUpperCase()
  switch (norm) {
    case 'STRONG_CASE':
    case 'CONTEST':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Contest', dot: '#3FA796' }
    case 'ACCEPT':
    case 'APPROVE':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Approve', dot: '#3FA796' }
    case 'DECISION_RECORDED':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Decision Recorded', dot: '#3FA796' }
    case 'WEAK_CASE':
    case 'REQUEST_MORE_EVIDENCE':
    case 'EVIDENCE_REQUESTED':
      return { edgeClass: 'verdict-edge-amber', badgeClass: 'badge-amber', label: 'Evidence Requested', dot: '#E0A339' }
    case 'HUMAN_REVIEW':
    case 'ESCALATE':
    case 'ESCALATED':
      return { edgeClass: 'verdict-edge-red', badgeClass: 'badge-red', label: 'Escalated', dot: '#D6483C' }
    case 'INVESTIGATING':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Investigating?', dot: '#5B6B7C' }
    case 'PENDING_REVIEW':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Pending Review', dot: '#5B6B7C' }
    case 'NEW':
    case 'OPEN':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Open', dot: '#5B6B7C' }
    case 'ACTION_REQUIRED':
      return { edgeClass: 'verdict-edge-amber', badgeClass: 'badge-amber', label: 'Action Required', dot: '#E0A339' }
    case 'UNDER_REVIEW':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Under Review', dot: '#5B6B7C' }
    case 'WON':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Won', dot: '#3FA796' }
    case 'LOST':
      return { edgeClass: 'verdict-edge-red', badgeClass: 'badge-red', label: 'Lost', dot: '#D6483C' }
    case 'CLOSED':
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: 'Closed', dot: '#5B6B7C' }
    case 'RESOLVED':
      return { edgeClass: 'verdict-edge-teal', badgeClass: 'badge-teal', label: 'Resolved', dot: '#3FA796' }
    default:
      return { edgeClass: 'verdict-edge-slate', badgeClass: 'badge-slate', label: status ?? 'Unknown', dot: '#5B6B7C' }
  }
}

export function lifecycleStatus(status: CaseStatus | string, recommendation: string | null, finalAction: string | null): string {
  if (finalAction) return status
  const norm = (status ?? '').toString().toUpperCase()
  if (['DECISION_RECORDED', 'RESOLVED', 'CLOSED', 'EVIDENCE_REQUESTED', 'ESCALATED'].includes(norm)) {
    return norm.toLowerCase()
  }
  switch (recommendation?.trim().toUpperCase()) {
    case 'ESCALATE': return 'escalated'
    case 'REQUEST_MORE_EVIDENCE': return 'evidence_requested'
    default: return 'pending_review'
  }
}

export function aiRecommendationLabel(status: CaseStatus | string | null | undefined): string {
  const norm = (status ?? '').toString().toUpperCase()
  switch (norm) {
    case 'STRONG_CASE':
    case 'CONTEST': return 'CONTEST'
    case 'ACCEPT':
    case 'APPROVE': return 'APPROVE'
    case 'WEAK_CASE':
    case 'REQUEST_MORE_EVIDENCE': return 'REQUEST MORE EVIDENCE'
    case 'HUMAN_REVIEW': return 'HUMAN REVIEW'
    case 'ESCALATE': return 'ESCALATE'
    case 'NEW':
    case 'OPEN': return 'PENDING'
    case 'INVESTIGATING': return 'INVESTIGATING?'
    default: return status ? status.toUpperCase().replace(/_/g, ' ') : '?'
  }
}

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

export function getAgentToolCalls(audit: AuditEntry[]): { tool: string; timestamp: string }[] {
  return audit
    .filter(a => a.step === 'agent_tool_called')
    .map(a => ({
      tool: (a.detail?.tool_name as string) ?? (a.detail?.tool as string) ?? 'unknown',
      timestamp: a.timestamp,
    }))
}

export function evidenceProvenance(evidenceType: string): 'razorpay' | 'merchant' | 'ai' {
  const t = evidenceType.toLowerCase()
  if (t.includes('payment') || t.includes('refund') || t.includes('razorpay')) return 'razorpay'
  if (t.includes('ai') || t.includes('analysis') || t.includes('finding')) return 'ai'
  return 'merchant'
}

export function isWebhookOrigin(audit: AuditEntry[]): boolean {
  return audit.some(a => a.step === 'webhook_case_created')
}

export function isDemoCase(transactionId: string): boolean {
  return transactionId.startsWith('DEMO_TXN_') || transactionId.startsWith('DEMO_SCN_')
}

export function formatDisputeReason(reason: string): string {
  return reason
    .split(/[_\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

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

export function shortTxn(txn: string): string {
  if (txn.length <= 22) return txn.toUpperCase()
  return `${txn.slice(0, 14).toUpperCase()}\u2026${txn.slice(-4).toUpperCase()}`
}
