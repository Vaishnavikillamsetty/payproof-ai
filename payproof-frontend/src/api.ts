import type { Case, CaseDetail, AuditEntry, EvalMetrics, Evidence, EvidenceUploadPayload } from './types'

const BASE = import.meta.env.VITE_API_URL || '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const reviewerId = localStorage.getItem('payproof_reviewer_id') || 'analyst_current'
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      'X-Reviewer-Id': reviewerId,
    },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export function warmBackend(): void {
  fetch(`${BASE.replace(/\/+$/, '')}/health`).catch(() => {})
}

export const api = {
  getCases: (): Promise<Case[]> =>
    request('/cases/'),

  getCase: (id: string): Promise<CaseDetail> =>
    request(`/cases/${id}`),

  resetDemoCases: async (): Promise<any> =>
    request('/cases/demo-reset', { method: 'DELETE' }),

  reviewCase: (id: string, action: string, notes: string, reviewerId?: string): Promise<CaseDetail> =>
    request(`/cases/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ action, notes, reviewer_id: reviewerId }),
    }),

  resolveCase: (id: string, notes: string = '', reviewerId?: string): Promise<CaseDetail> =>
    request(`/cases/${id}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ notes, reviewer_id: reviewerId }),
    }),

  closeCase: (id: string, notes: string = '', reviewerId?: string): Promise<CaseDetail> =>
    request(`/cases/${id}/close`, {
      method: 'POST',
      body: JSON.stringify({ notes, reviewer_id: reviewerId }),
    }),

  uploadEvidence: (id: string, payload: EvidenceUploadPayload): Promise<Evidence> =>
    request(`/cases/${id}/evidence`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getAudit: (id: string): Promise<AuditEntry[]> =>
    request(`/cases/${id}/audit`),

  getMetrics: (): Promise<EvalMetrics> =>
    request('/metrics/'),
    
  getDemoInfo: (transaction_id: string): Promise<{is_demo: boolean, expected_amount?: number}> =>
    request(`/cases/demo-info/${transaction_id}`),

  createCase: (body: {
    transaction_id: string
    dispute_reason: string
    customer_claim: string
    merchant_id: string
    amount: number
  }): Promise<Case> =>
    request('/cases/', { method: 'POST', body: JSON.stringify(body) }),
}
