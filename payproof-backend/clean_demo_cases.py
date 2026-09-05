import sys
sys.path.insert(0, '.')
from app.db.session import SessionLocal
from app.db.models import Case, Evidence, AuditLog, RuleFlag, Claim

db = SessionLocal()
demo_cases = db.query(Case).filter(
    (Case.transaction_id.like("DEMO_SCN_%"))
).all()

count = len(demo_cases)
for c in demo_cases:
    db.query(AuditLog).filter(AuditLog.case_id == c.id).delete(synchronize_session=False)
    db.query(Evidence).filter(Evidence.case_id == c.id).delete(synchronize_session=False)
    db.query(RuleFlag).filter(RuleFlag.case_id == c.id).delete(synchronize_session=False)
    db.query(Claim).filter(Claim.case_id == c.id).delete(synchronize_session=False)
    db.delete(c)

db.commit()
print(f"Deleted {count} demo cases.")
