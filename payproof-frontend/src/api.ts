import type { Case, CaseDetail, AuditEntry, EvalMetrics } from './types'

const BASE = import.meta.env.VITE_API_URL || '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  getCases: (): Promise<Case[]> =>
    request('/cases/'),

  getCase: (id: string): Promise<CaseDetail> =>
    request(`/cases/${id}`),

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
