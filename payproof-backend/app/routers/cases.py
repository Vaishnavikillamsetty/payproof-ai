from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db.session import get_db
from app.db.models import Case
from app.schemas import CaseCreate, CaseResponse, CaseDetailResponse

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("/", response_model=CaseResponse)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    db_case = Case(
        transaction_id=case_in.transaction_id,
        dispute_reason=case_in.dispute_reason,
        customer_claim=case_in.customer_claim,
        merchant_id=case_in.merchant_id,
        amount=case_in.amount,
        status="new"
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("/", response_model=List[CaseResponse])
def get_cases(db: Session = Depends(get_db)):
    return db.query(Case).all()

@router.get("/{id}", response_model=CaseDetailResponse)
def get_case(id: UUID, db: Session = Depends(get_db)):
    db_case = db.query(Case).filter(Case.id == id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case
