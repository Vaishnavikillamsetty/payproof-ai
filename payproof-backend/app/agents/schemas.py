"""
Strict Pydantic schemas for the DisputeInvestigationAgent output.

Every agent recommendation MUST validate against AgentRecommendation
before being stored or acted upon.  Invalid AI output is caught here
and triggers the deterministic fallback path.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, field_validator


class RecommendedAction(str, Enum):
    ACCEPT = "ACCEPT"
    CONTEST = "CONTEST"
    ESCALATE = "ESCALATE"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvidenceStrength(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SourceStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    LIMITED = "LIMITED"


class Finding(BaseModel):
    """One structured, evidence-grounded finding. No raw chain-of-thought."""
    finding: str
    source: str
    importance: str  # "high", "medium", "low"
    verified: bool = False  # Is this a definitively verified API fact or just a finding?


class AgentRecommendation(BaseModel):
    """Strictly validated output from the DisputeInvestigationAgent."""
    recommended_action: RecommendedAction
    confidence: float
    risk_level: RiskLevel
    evidence_strength: EvidenceStrength
    summary: str
    key_findings: List[Finding]
    missing_evidence: List[str]
    contradictions: List[str]
    human_approval_required: bool = True  # Always true — safety default
    source_status: SourceStatus
    ai_status: str = "OK"  # "OK" or "FALLBACK"

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be 0.0–1.0, got {v}")
        return round(v, 4)
