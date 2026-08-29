"""
Evidence Collector — deterministic, no LLM.
Fetches all evidence rows for a case from the database.
The orchestrator passes these to the rule engine and verifier.
"""
from sqlalchemy.orm import Session
from app.db.models import Evidence


def collect_evidence(case_id, db: Session) -> list[Evidence]:
    """Return all Evidence rows associated with a case, ordered by event_timestamp."""
    return (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.event_timestamp.nullslast())
        .all()
    )
