from pydantic import BaseModel, ConfigDict, UUID4, model_validator
from typing import Any, List, Optional
from datetime import datetime
from app.evidence_categories import compute_category_coverage, evaluate_evidence_strength


class CaseCreate(BaseModel):
    transaction_id: str
    dispute_reason: str
    customer_claim: str
    merchant_id: str
    amount: float


class HumanReviewRequest(BaseModel):
    action: str  # approve, contest, request_more_evidence
    notes: str = ""
    reviewer_id: Optional[str] = None


class CaseActionRequest(BaseModel):
    notes: str = ""
    reviewer_id: Optional[str] = None


class EvidenceUploadRequest(BaseModel):
    category: Optional[str] = None  # transaction, customer, delivery, merchant
    evidence_type: str = "custom_document"
    filename: Optional[str] = None
    description: Optional[str] = None
    content: dict = {}
    file_base64: Optional[str] = None
    verification_status: str = "unverified"


class CaseResponse(BaseModel):
    id: UUID4
    transaction_id: str
    dispute_reason: str
    customer_claim: str
    merchant_id: str
    amount: float
    status: str
    ai_recommendation: Optional[str] = None
    ai_explanation: Optional[str] = None
    human_decision: Optional[str] = None
    reviewer_id: Optional[str] = None
    decision_timestamp: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    evidence_strength: Optional[str] = None
    final_action: Optional[str] = None
    contradiction_detected: bool = False
    currency: str = "UNKNOWN"
    completeness_score: Optional[float] = None
    overall_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    evidence_types: List[str] = []
    categories_available: List[str] = []
    category_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def populate_evidence_metadata(cls, data):
        # Extract pre-attached metadata if provided by optimized queries
        if hasattr(data, '__dict__'):
            d = data.__dict__
            # If categories_available was already pre-calculated
            if 'categories_available' in d and 'category_count' in d:
                return data
            
            # Derive from evidence relationship if loaded
            if hasattr(data, 'evidence') and data.evidence is not None:
                ev_list = data.evidence
                d.setdefault('evidence_types', [e.evidence_type for e in ev_list])
                cats, count = compute_category_coverage(ev_list)
                d.setdefault('categories_available', cats)
                d.setdefault('category_count', count)
                if not getattr(data, 'evidence_strength', None):
                    d['evidence_strength'] = evaluate_evidence_strength(ev_list, cats, getattr(data, 'contradiction_detected', False))
            else:
                d.setdefault('evidence_types', d.get('evidence_types', []))
                d.setdefault('categories_available', d.get('categories_available', []))
                d.setdefault('category_count', len(d.get('categories_available', [])))
        return data


class EvidenceResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    evidence_type: str
    category: Optional[str] = None
    source_id: Optional[str] = None
    filename: Optional[str] = None
    description: Optional[str] = None
    verification_status: Optional[str] = "unverified"
    content: dict
    event_timestamp: Optional[datetime] = None
    collected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    claim_text: str
    supporting_evidence_ids: Optional[List[UUID4]] = None
    contradicting_evidence_ids: Optional[List[UUID4]] = None
    confidence: Optional[float] = None
    verdict: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RuleFlagResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    rule_name: str
    triggered: bool
    detail: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CaseDetailResponse(CaseResponse):
    evidence: List[EvidenceResponse] = []
    claims: List[ClaimResponse] = []
    rule_flags: List[RuleFlagResponse] = []


class AuditLogResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    step: str
    detail: Optional[Any] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
