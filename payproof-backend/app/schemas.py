from pydantic import BaseModel, ConfigDict, UUID4
from typing import List, Optional
from datetime import datetime

class CaseCreate(BaseModel):
    transaction_id: str
    dispute_reason: str
    customer_claim: str
    merchant_id: str
    amount: float

class CaseResponse(BaseModel):
    id: UUID4
    transaction_id: str
    dispute_reason: str
    customer_claim: str
    merchant_id: str
    amount: float
    status: str
    completeness_score: Optional[float] = None
    overall_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

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
