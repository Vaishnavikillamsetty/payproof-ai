import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import engine, SessionLocal
from app.db.models import (
    Base, PaymentGatewayRecord, DeliveryRecord, OtpLog, CommunicationLog
)

def init_db():
    # Create the new tables
    Base.metadata.create_all(bind=engine)

def seed_db():
    db = SessionLocal()
    
    # Clear existing seed data to allow re-runs
    db.query(PaymentGatewayRecord).delete()
    db.query(DeliveryRecord).delete()
    db.query(OtpLog).delete()
    db.query(CommunicationLog).delete()

    now = datetime.now(timezone.utc)
    
    # ---------------------------------------------------------
    # Scenario 1: Strong Case (Full Evidence)
    # ---------------------------------------------------------
    txn_strong = "DEMO_TXN_STRONG_1"
    
    db.add(PaymentGatewayRecord(
        transaction_id=txn_strong, amount=299.99, currency="USD", status="success",
        timestamp=now - timedelta(days=5)
    ))
    db.add(DeliveryRecord(
        transaction_id=txn_strong, tracking_number="TRK_STRONG_1", status="delivered",
        signed_by="Customer", address_match=True, notes="Left at door",
        timestamp=now - timedelta(days=2)
    ))
    db.add(OtpLog(
        transaction_id=txn_strong, verified=True, ip_address="192.168.1.5",
        timestamp=now - timedelta(days=5, minutes=2)
    ))
    db.add(CommunicationLog(
        transaction_id=txn_strong, channel="email", message="Please cancel my subscription.",
        has_attachments=False, timestamp=now - timedelta(days=1)
    ))

    # ---------------------------------------------------------
    # Scenario 2: Weak Case / Review (Sparse - only payment)
    # ---------------------------------------------------------
    txn_weak = "DEMO_TXN_WEAK_1"
    
    db.add(PaymentGatewayRecord(
        transaction_id=txn_weak, amount=49.50, currency="USD", status="success",
        timestamp=now - timedelta(days=3)
    ))

    # ---------------------------------------------------------
    # Scenario 3: Human Review (Contradiction - "product not received" but delivered)
    # ---------------------------------------------------------
    txn_contradiction = "DEMO_TXN_REVIEW_1"
    
    db.add(PaymentGatewayRecord(
        transaction_id=txn_contradiction, amount=899.00, currency="USD", status="success",
        timestamp=now - timedelta(days=10)
    ))
    db.add(DeliveryRecord(
        transaction_id=txn_contradiction, tracking_number="TRK_REVIEW_1", status="delivered",
        signed_by="Front Desk", address_match=True, notes="Signed by receptionist",
        timestamp=now - timedelta(days=4)
    ))

    # ---------------------------------------------------------
    # Scenario 4: Human Review (Insufficient / Empty)
    # ---------------------------------------------------------
    # We don't add any records for this ID.
    txn_empty = "DEMO_TXN_EMPTY_1"
    
    
    # Add a few more variants to pad out the 30-40 cases requirement
    for i in range(2, 10):
        # Additional Strong cases
        db.add(PaymentGatewayRecord(
            transaction_id=f"DEMO_TXN_STRONG_{i}", amount=100.0+i, currency="USD", status="success",
            timestamp=now - timedelta(days=i)
        ))
        db.add(CommunicationLog(
            transaction_id=f"DEMO_TXN_STRONG_{i}", channel="chat", message="Item arrived broken.",
            has_attachments=True, timestamp=now - timedelta(days=1)
        ))
        
        # Additional Weak cases
        db.add(PaymentGatewayRecord(
            transaction_id=f"DEMO_TXN_WEAK_{i}", amount=20.0+i, currency="USD", status="success",
            timestamp=now - timedelta(days=i)
        ))

    db.commit()
    db.close()
    
    print("Seed complete!")
    print("\nHere are 4 known transaction IDs you can use for your live demo:")
    print(f"1. Strong Case (Auto-Resolve)       -> {txn_strong}")
    print(f"2. Weak Case (Sparse Evidence)      -> {txn_weak}")
    print(f"3. Human Review (Contradiction)     -> {txn_contradiction}  (Use with reason 'product not received')")
    print(f"4. Human Review (No Evidence Found) -> {txn_empty}")

if __name__ == "__main__":
    init_db()
    seed_db()
