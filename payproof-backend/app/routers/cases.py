from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db.session import get_db
from app.schemas import CaseCreate, CaseResponse, CaseDetailResponse
import datetime

router = APIRouter(prefix="/cases", tags=["cases"])

# Dummy data generation for phase 1
DUMMY_ID = "123e4567-e89b-12d3-a456-426614174000"

@router.post("/", response_model=CaseResponse)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    # Currently a dummy response
    return {
        "id": DUMMY_ID,
        "transaction_id": case_in.transaction_id,
        "dispute_reason": case_in.dispute_reason,
        "customer_claim": case_in.customer_claim,
        "merchant_id": case_in.merchant_id,
        "amount": case_in.amount,
        "status": "new",
        "completeness_score": None,
        "overall_confidence": None,
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }

@router.get("/", response_model=List[CaseResponse])
def get_cases(db: Session = Depends(get_db)):
    return [{
        "id": DUMMY_ID,
        "transaction_id": "txn_abc123",
        "dispute_reason": "product not received",
        "customer_claim": "I ordered a laptop but it never arrived.",
        "merchant_id": "merch_xyz789",
        "amount": 999.99,
        "status": "new",
        "completeness_score": None,
        "overall_confidence": None,
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }]

@router.get("/{id}", response_model=CaseDetailResponse)
def get_case(id: UUID, db: Session = Depends(get_db)):
    return {
        "id": id,
        "transaction_id": "txn_abc123",
        "dispute_reason": "product not received",
        "customer_claim": "I ordered a laptop but it never arrived.",
        "merchant_id": "merch_xyz789",
        "amount": 999.99,
        "status": "new",
        "completeness_score": None,
        "overall_confidence": None,
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now(),
        "evidence": [],
        "claims": [],
        "rule_flags": []
    }
