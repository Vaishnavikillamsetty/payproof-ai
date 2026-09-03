import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import engine, SessionLocal
from app.db.models import (
    Base, PaymentGatewayRecord, DeliveryRecord, OtpLog, CommunicationLog
)

def init_db():
    Base.metadata.create_all(bind=engine)

def _add_strong(db, txn, now, amount, comm_msg=""):
    db.add(PaymentGatewayRecord(transaction_id=txn, amount=amount, currency="USD", status="success", timestamp=now - timedelta(days=5)))
    db.add(DeliveryRecord(transaction_id=txn, tracking_number=f"TRK_{txn}", status="delivered", signed_by="Customer", address_match=True, notes="Signed", timestamp=now - timedelta(days=2)))
    db.add(OtpLog(transaction_id=txn, verified=True, ip_address="192.168.1.5", timestamp=now - timedelta(days=5)))
    if comm_msg:
        db.add(CommunicationLog(transaction_id=txn, channel="email", message=comm_msg, has_attachments=False, timestamp=now - timedelta(days=1)))

def _add_weak(db, txn, now, amount):
    db.add(PaymentGatewayRecord(transaction_id=txn, amount=amount, currency="USD", status="success", timestamp=now - timedelta(days=5)))

def _add_contradiction(db, txn, now, amount, delivery_status="delivered", delivery_signed="Front Desk", comm_msg=""):
    db.add(PaymentGatewayRecord(transaction_id=txn, amount=amount, currency="USD", status="success", timestamp=now - timedelta(days=5)))
    db.add(DeliveryRecord(transaction_id=txn, tracking_number=f"TRK_{txn}", status=delivery_status, signed_by=delivery_signed, address_match=True, notes="Accepted", timestamp=now - timedelta(days=3)))
    if comm_msg:
        db.add(CommunicationLog(transaction_id=txn, channel="chat", message=comm_msg, has_attachments=False, timestamp=now - timedelta(days=1)))

def _add_empty(db, txn, now, amount):
    db.add(PaymentGatewayRecord(transaction_id=txn, amount=amount, currency="USD", status="success", timestamp=now - timedelta(days=5)))

def seed_db():
    db = SessionLocal()
    
    db.query(PaymentGatewayRecord).delete()
    db.query(DeliveryRecord).delete()
    db.query(OtpLog).delete()
    db.query(CommunicationLog).delete()

    now = datetime.now(timezone.utc)
    
    _add_strong(db, "DEMO_SCN_01", now, 299.99, comm_msg="Please cancel my subscription before renewal.")
    _add_strong(db, "DEMO_SCN_02", now, 129.50)
    _add_strong(db, "DEMO_SCN_03", now, 599.00, comm_msg="Where is my item?")
    
    # 4. Strong: Duplicate charge (add extra payment record)
    _add_strong(db, "DEMO_SCN_04", now, 45.00)
    db.add(PaymentGatewayRecord(transaction_id="DEMO_SCN_04", amount=45.00, currency="USD", status="success", timestamp=now - timedelta(days=5, minutes=2)))
    
    _add_weak(db, "DEMO_SCN_05", now, 120.00)
    
    # 6. Weak: Missing comms
    db.add(PaymentGatewayRecord(transaction_id="DEMO_SCN_06", amount=89.99, currency="USD", status="success", timestamp=now - timedelta(days=5)))
    db.add(DeliveryRecord(transaction_id="DEMO_SCN_06", tracking_number="TRK_06", status="shipped", signed_by="", address_match=True, notes="In transit", timestamp=now - timedelta(days=1)))
    
    _add_weak(db, "DEMO_SCN_07", now, 25.00)
    
    # 8. Weak: Partial evidence
    db.add(PaymentGatewayRecord(transaction_id="DEMO_SCN_08", amount=150.00, currency="USD", status="success", timestamp=now - timedelta(days=5)))
    db.add(OtpLog(transaction_id="DEMO_SCN_08", verified=False, ip_address="10.0.0.1", timestamp=now - timedelta(days=5)))
    
    _add_contradiction(db, "DEMO_SCN_09", now, 200.00, delivery_status="delivered", delivery_signed="Customer", comm_msg="I received this yesterday but it's broken.")
    _add_contradiction(db, "DEMO_SCN_10", now, 850.00, delivery_status="delivered", delivery_signed="Front Desk")
    
    # 11. Contradiction: Refund status 
    db.add(PaymentGatewayRecord(transaction_id="DEMO_SCN_11", amount=199.99, currency="USD", status="success", timestamp=now - timedelta(days=5)))
    db.add(CommunicationLog(transaction_id="DEMO_SCN_11", channel="email", message="We have processed your refund.", has_attachments=False, timestamp=now - timedelta(days=1)))
    
    # 12. Contradiction: Multiple auth signals conflict
    db.add(PaymentGatewayRecord(transaction_id="DEMO_SCN_12", amount=1100.00, currency="USD", status="success", timestamp=now - timedelta(days=5)))
    db.add(OtpLog(transaction_id="DEMO_SCN_12", verified=True, ip_address="192.168.1.5", timestamp=now - timedelta(days=5)))
    db.add(OtpLog(transaction_id="DEMO_SCN_12", verified=False, ip_address="203.0.113.42", timestamp=now - timedelta(days=5, minutes=10)))
    
    _add_empty(db, "DEMO_SCN_13", now, 45.00)
    _add_empty(db, "DEMO_SCN_14", now, 14.99)
    _add_empty(db, "DEMO_SCN_15", now, 75.00)

    db.commit()
    db.close()
    
    print("Seed complete! Created DEMO_SCN_01 through DEMO_SCN_15.")

if __name__ == "__main__":
    init_db()
    seed_db()
