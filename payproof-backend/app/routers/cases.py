import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Case, Evidence
from app.db.session import get_db
from app.agents.external_systems import get_demo_expected_amount
from app.orchestrator import run_pipeline
from app.schemas import AuditLogResponse, CaseCreate, CaseDetailResponse, CaseResponse
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/", response_model=CaseResponse, status_code=201)
def create_case(
    case_in: CaseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Submit a new dispute.
    """
    final_amount = case_in.amount

    # For seeded demo transactions, the backend is authoritative.
    # Automatically override the user's amount with the exact seeded amount.
    demo_amount = get_demo_expected_amount(db, case_in.transaction_id)
    if demo_amount is not None:
        final_amount = demo_amount
    else:
        # For arbitrary/dynamic transactions, the user must provide a valid amount > 0.
        if final_amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0.")

    db_case = Case(
        transaction_id=case_in.transaction_id,
        dispute_reason=case_in.dispute_reason,
        customer_claim=case_in.customer_claim,
        merchant_id=case_in.merchant_id,
        amount=final_amount,
        status="new",
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    background_tasks.add_task(run_pipeline, db_case.id)

    return db_case


@router.get("/demo-info/{transaction_id}")
def get_demo_info(transaction_id: str, db: Session = Depends(get_db)):
    """
    Check if a transaction ID corresponds to a seeded demo case,
    and return its authoritative expected amount.
    """
    expected_amount = get_demo_expected_amount(db, transaction_id)
    if expected_amount is not None:
        return {"is_demo": True, "expected_amount": expected_amount}
    return {"is_demo": False}


@router.get("/", response_model=List[CaseResponse])
def get_cases(db: Session = Depends(get_db)):
    return (
        db.query(Case)
        .options(joinedload(Case.evidence))
        .order_by(Case.created_at.desc())
        .all()
    )


@router.get("/{id}", response_model=CaseDetailResponse)
def get_case(id: UUID, db: Session = Depends(get_db)):
    db_case = db.query(Case).filter(Case.id == id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case


@router.get("/{id}/audit", response_model=List[AuditLogResponse])
def get_audit(id: UUID, db: Session = Depends(get_db)):
    """Return the full, immutable audit trail for a case in chronological order."""
    # Verify the case exists first
    if not db.query(Case).filter(Case.id == id).first():
        raise HTTPException(status_code=404, detail="Case not found")

    return (
        db.query(AuditLog)
        .filter(AuditLog.case_id == id)
        .order_by(AuditLog.timestamp)
        .all()
    )
