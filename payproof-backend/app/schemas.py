from pydantic import BaseModel, ConfigDict, UUID4, field_validator, model_validator
from typing import Any, List, Optional
from datetime import datetime


class CaseCreate(BaseModel):
    transaction_id: str
    dispute_reason: str
    customer_claim: str
    merchant_id: str
    amount: float


class HumanReviewRequest(BaseModel):
    action: str
    notes: str = ""


class CaseResponse(BaseModel):
    id: UUID4
    transaction_id: str
    dispute_reason: str
    customer_claim: str
    merchant_id: str
    amount: float
    status: str
    ai_recommendation: Optional[str] = None
    final_action: Optional[str] = None
    contradiction_detected: bool = False
    currency: str = "USD"
    completeness_score: Optional[float] = None
    overall_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    # Derived from the evidence relationship — allows Dashboard to show
    # category availability without a separate evidence fetch (no N+1).
    evidence_types: List[str] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def populate_evidence_types(cls, data):
        # If evidence_types was pre-set by the optimized GET /cases/ query, use it.
        if hasattr(data, '__dict__') and 'evidence_types' in data.__dict__:
            return data
        # Fallback: derive from the ORM relationship (used by single-case detail views)
        if hasattr(data, 'evidence'):
            data.__dict__.setdefault('evidence_types', [e.evidence_type for e in (data.evidence or [])])
        return data


class EvidenceResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    evidence_type: str
    source_id: Optional[str]
    content: dict
    event_timestamp: Optional[datetime]
    collected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    claim_text: str
    supporting_evidence_ids: Optional[List[UUID4]]
    contradicting_evidence_ids: Optional[List[UUID4]]
    confidence: Optional[float]
    verdict: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class RuleFlagResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    rule_name: str
    triggered: bool
    detail: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class CaseDetailResponse(CaseResponse):
    evidence: List[EvidenceResponse] = []
    claims: List[ClaimResponse] = []
    rule_flags: List[RuleFlagResponse] = []


class AuditLogResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    step: str
    detail: Optional[Any]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
