from sqlalchemy import Column, String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String, nullable=False)
    dispute_reason = Column(String, nullable=False)
    customer_claim = Column(String, nullable=False)
    merchant_id = Column(String, nullable=False)
    amount = Column(Numeric, nullable=False)
    status = Column(String, nullable=False, default="new")
    completeness_score = Column(Numeric, nullable=True)
    overall_confidence = Column(Numeric, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="case", cascade="all, delete-orphan")
    rule_flags = relationship("RuleFlag", back_populates="case", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"))
    evidence_type = Column(String, nullable=False)
    source_id = Column(String, nullable=True)
    content = Column(JSONB, nullable=False)
    event_timestamp = Column(DateTime(timezone=True), nullable=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    case = relationship("Case", back_populates="evidence")

class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"))
    claim_text = Column(String, nullable=False)
    supporting_evidence_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    contradicting_evidence_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    confidence = Column(Numeric, nullable=True)
    verdict = Column(String, nullable=True)

    case = relationship("Case", back_populates="claims")

class RuleFlag(Base):
    __tablename__ = "rule_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"))
    rule_name = Column(String, nullable=False)
    triggered = Column(Boolean, nullable=False)
    detail = Column(String, nullable=True)

    case = relationship("Case", back_populates="rule_flags")

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"))
    step = Column(String, nullable=False)
    detail = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
