import sys
sys.path.insert(0, '.')
from app.db.session import SessionLocal
from app.db.models import Case, Evidence
from app.orchestrator import run_pipeline

db = SessionLocal()
case = db.query(Case).filter_by(transaction_id="DEMO_SCN_DUP").first()
case.status = "new"

# clear existing rule flags and audit logs
from app.db.models import RuleFlag, AuditLog
db.query(RuleFlag).filter_by(case_id=case.id).delete()
db.query(AuditLog).filter_by(case_id=case.id).delete()

# Add duplicate payments
ev1 = Evidence(case_id=case.id, evidence_type="payment", source_id="pay_1", content={"amount": 100.0, "status": "success"})
ev2 = Evidence(case_id=case.id, evidence_type="payment", source_id="pay_2", content={"amount": 100.0, "status": "success"})
db.add(ev1)
db.add(ev2)
db.commit()

run_pipeline(case.id, db)
print("Pipeline run successfully.")
