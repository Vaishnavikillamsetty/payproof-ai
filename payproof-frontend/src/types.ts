// Mirrors the Pydantic response models from the FastAPI backend.

export type CaseStatus =
  | 'new'
  | 'OPEN'
  | 'open'
  | 'investigating'
  | 'INVESTIGATING'
  | 'pending_review'
  | 'strong_case'
  | 'weak_case'
  | 'human_review'
  | 'DECISION_RECORDED'
  | 'decision_recorded'
  | 'resolved'
  | 'RESOLVED'
  | 'request_more_evidence'
  | 'evidence_requested'
  | 'EVIDENCE_REQUESTED'
  | 'escalate'
  | 'escalated'
  | 'ESCALATED'
  | 'accept'
  | 'contest'
  | 'action_required'
  | 'under_review'
  | 'won'
  | 'lost'
  | 'closed'
  | 'CLOSED'

export interface Case {
  id: string
  transaction_id: string
  dispute_reason: string
  customer_claim: string
  merchant_id: string
  amount: number
  currency: string
  status: CaseStatus
  ai_recommendation: string | null
  ai_explanation?: string | null
  human_decision?: string | null
  reviewer_id?: string | null
  decision_timestamp?: string | null
  reviewer_notes?: string | null
  evidence_strength?: string | null
  categories_available?: string[]
  category_count?: number
  final_action: string | null
  contradiction_detected: boolean
  completeness_score: number | null
  overall_confidence: number | null
  created_at: string
  updated_at: string
  /** Evidence type names for the case — populated by the list endpoint */
  evidence_types: string[]
}

export interface Evidence {
  id: string
  case_id: string
  evidence_type: string
  category?: string | null
  source_id: string | null
  filename?: string | null
  description?: string | null
  verification_status?: string | null
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

export interface EvalMetrics {
  confusion_matrix: {
    true_positives: number
    false_positives: number
    true_negatives: number
    false_negatives: number
    total: number
  }
  rates: {
    precision: number
    recall: number
  }
  business_impact: {
    wasted_reviews: number
    cost_statement: string
    unsafe_resolves: number
    unsafe_statement: string
  }
}

export interface EvidenceUploadPayload {
  category?: 'transaction' | 'customer' | 'delivery' | 'merchant' | string
  evidence_type: string
  filename?: string
  description?: string
  file_base64?: string
  verification_status?: string
  content?: Record<string, unknown>
}
