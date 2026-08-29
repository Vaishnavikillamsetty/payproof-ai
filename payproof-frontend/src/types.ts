// Mirrors the Pydantic response models from the FastAPI backend.

export type CaseStatus =
  | 'new'
  | 'investigating'
  | 'strong_case'
  | 'weak_case'
  | 'human_review'
  | 'resolved'

export interface Case {
  id: string
  transaction_id: string
  dispute_reason: string
  customer_claim: string
  merchant_id: string
  amount: number
  status: CaseStatus
  completeness_score: number | null
  overall_confidence: number | null
  created_at: string
  updated_at: string
}

export interface Evidence {
  id: string
  case_id: string
  evidence_type: string
  source_id: string | null
  content: Record<string, unknown>
  event_timestamp: string | null
  collected_at: string
}

export interface Claim {
  id: string
  case_id: string
  claim_text: string
  supporting_evidence_ids: string[]
  contradicting_evidence_ids: string[]
  confidence: number | null
  verdict: 'supported' | 'contradicted' | 'unverifiable' | null
}

export interface RuleFlag {
  id: string
  case_id: string
  rule_name: string
  triggered: boolean
  detail: string | null
}

export interface CaseDetail extends Case {
  evidence: Evidence[]
  claims: Claim[]
  rule_flags: RuleFlag[]
}

export interface AuditEntry {
  id: string
  case_id: string
  step: string
  detail: Record<string, unknown> | null
  timestamp: string
}
