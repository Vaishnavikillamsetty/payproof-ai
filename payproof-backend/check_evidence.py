import sys

sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.db.models import (
    PaymentGatewayRecord,
    DeliveryRecord,
    OtpLog,
    CommunicationLog,
    Case,
    Evidence,
)

db = SessionLocal()

try:
    print("\n========== DATABASE EVIDENCE AUDIT ==========\n")

    # Check all evidence source tables
    print("=== PAYMENT GATEWAY RECORDS ===")
    rows = db.query(PaymentGatewayRecord).all()
    print(f"Total: {len(rows)}")
    for r in rows:
        print(
            f"Transaction: {r.transaction_id} | "
            f"Amount: {getattr(r, 'amount', 'N/A')}"
        )

    print("\n=== DELIVERY RECORDS ===")
    rows = db.query(DeliveryRecord).all()
    print(f"Total: {len(rows)}")
    for r in rows:
        print(f"Transaction: {getattr(r, 'transaction_id', 'N/A')}")
        print(f"Data: {r.__dict__}")

    print("\n=== OTP LOGS ===")
    rows = db.query(OtpLog).all()
    print(f"Total: {len(rows)}")
    for r in rows:
        print(f"Transaction: {getattr(r, 'transaction_id', 'N/A')}")
        print(f"Data: {r.__dict__}")

    print("\n=== COMMUNICATION LOGS ===")
    rows = db.query(CommunicationLog).all()
    print(f"Total: {len(rows)}")
    for r in rows:
        print(f"Transaction: {getattr(r, 'transaction_id', 'N/A')}")
        print(f"Data: {r.__dict__}")

    print("\n========== CASE AUDIT ==========\n")

    cases = db.query(Case).order_by(Case.created_at.desc()).all()

    print(f"Total cases: {len(cases)}\n")

    for c in cases:
        ev_count = (
            db.query(Evidence)
            .filter(Evidence.case_id == c.id)
            .count()
        )

        print("-" * 70)
        print(f"CASE ID:        {c.id}")
        print(f"TRANSACTION ID: {c.transaction_id}")
        print(f"STATUS:         {c.status}")
        print(f"CASE EVIDENCE:  {ev_count}")

        evidence_rows = (
            db.query(Evidence)
            .filter(Evidence.case_id == c.id)
            .all()
        )

        for ev in evidence_rows:
            print(f"  Evidence: {ev.__dict__}")

    print("\n========== SCENARIO 04 CHECK ==========\n")

    # Specifically inspect Scenario 04
    scenario_04_cases = (
        db.query(Case)
        .filter(Case.transaction_id.like("DEMO_SCN_04%"))
        .all()
    )

    print(f"Scenario 04 cases found: {len(scenario_04_cases)}")

    for c in scenario_04_cases:
        print(f"\nCase: {c.transaction_id}")
        print(f"Case ID: {c.id}")

        ev_count = (
            db.query(Evidence)
            .filter(Evidence.case_id == c.id)
            .count()
        )

        print(f"Attached Evidence rows: {ev_count}")

    print("\n=== SOURCE RECORDS FOR BASE ID DEMO_SCN_04 ===")

    for model, name in [
        (PaymentGatewayRecord, "PaymentGatewayRecord"),
        (DeliveryRecord, "DeliveryRecord"),
        (OtpLog, "OtpLog"),
        (CommunicationLog, "CommunicationLog"),
    ]:
        rows = (
            db.query(model)
            .filter(model.transaction_id == "DEMO_SCN_04")
            .all()
        )

        print(f"{name}: {len(rows)} record(s)")

        for row in rows:
            print(f"  {row.__dict__}")

finally:
    db.close()