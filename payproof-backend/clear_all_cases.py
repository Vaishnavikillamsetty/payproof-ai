from app.db.session import SessionLocal
from app.db.models import Case, Evidence, RuleFlag, Claim, AuditLog

db = SessionLocal()

try:
    audit = db.query(AuditLog).delete(synchronize_session=False)
    evidence = db.query(Evidence).delete(synchronize_session=False)
    flags = db.query(RuleFlag).delete(synchronize_session=False)
    claims = db.query(Claim).delete(synchronize_session=False)
    cases = db.query(Case).delete(synchronize_session=False)

    db.commit()

    print("================================")
    print("DATABASE CLEARED")
    print("================================")
    print(f"Cases deleted:      {cases}")
    print(f"Evidence deleted:   {evidence}")
    print(f"Rule flags deleted: {flags}")
    print(f"Claims deleted:     {claims}")
    print(f"Audit logs deleted: {audit}")
    print("================================")
    print("Ready for a fresh start.")

except Exception as e:
    db.rollback()
    print("ERROR:", e)

finally:
    db.close()