import sys
sys.path.insert(0, '.')
from app.db.session import SessionLocal
from app.db.models import PaymentGatewayRecord, DeliveryRecord, OtpLog, CommunicationLog, Case, Evidence

db = SessionLocal()

print("=== PaymentGatewayRecord ===")
rows = db.query(PaymentGatewayRecord).all()
print(f"Count: {len(rows)}")
for r in rows:
    print(f"  {r.transaction_id} -> amount={r.amount}")

print("\n=== Cases (first 20) ===")
cases = db.query(Case).order_by(Case.created_at.desc()).limit(20).all()
print(f"Total cases in DB: {db.query(Case).count()}")
for c in cases:
    ev_count = db.query(Evidence).filter(Evidence.case_id == c.id).count()
    print(f"  [{c.status:25s}] {c.transaction_id:35s}  ev={ev_count}")

db.close()
