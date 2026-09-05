"""
DATASET GENERATION SCRIPT

Transaction amounts and time-of-day timestamps are sampled from the Kaggle
"Credit Card Fraud Detection" (mlg-ulb/creditcardfraud) dataset for real-world
realism. The dispute scenarios, evidence structure, and ground-truth labels are
synthetically designed specifically for this project.
"""

import csv
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session  # noqa: E402 (after sys.path manipulation)

from app.db.models import AuditLog, Base, Case, Claim, Evidence, RuleFlag  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402

# Re-create tables if they don't exist
Base.metadata.create_all(bind=engine)

CATEGORIES = [
    "product not received",
    "product not as described",
    "duplicate charge",
    "subscription not cancelled",
    "unauthorized transaction"
]

LABELS = ["legitimate", "fraudulent", "ambiguous"]

def generate_cases(num_cases=180):
    db = SessionLocal()
    
    # Load amounts and times from Kaggle dataset
    csv_path = os.path.join(os.path.dirname(__file__), 'creditcard.csv')
    real_transactions = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                real_transactions.append((float(row['Time']), float(row['Amount'])))
        print(f"Loaded {len(real_transactions)} real transactions from Kaggle dataset for sampling.")
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        print("Please ensure creditcard.csv is in the data folder.")
        return
    
    # Optionally clear existing data for a fresh run
    # Order matters: child tables must be deleted before their parents
    db.query(Claim).delete()
    db.query(RuleFlag).delete()
    db.query(AuditLog).delete()
    db.query(Evidence).delete()
    db.query(Case).delete()
    db.commit()

    ground_truth = {}
    
    for i in range(num_cases):
        case_id = uuid.uuid4()
        category = random.choice(CATEGORIES)
        label = random.choice(LABELS)
        split = "test" if i >= 150 else "dev"
        
        ground_truth[str(case_id)] = {
            "label": label,
            "split": split,
            "category": category
        }
        
        sampled_time, sampled_amount = random.choice(real_transactions)
        
        # We sample amounts from the Kaggle dataset for realism instead of uniform random.
        # Note: We enforce a minimum of 1.00 to avoid ₹0.00 dispute edge cases.
        amount = max(1.0, round(sampled_amount, 2))
        
        # We use the Kaggle dataset's 'Time' (seconds) to get a realistic time-of-day distribution,
        # but spread the transactions over the last 10-60 days.
        random_day_offset = random.randint(10, 60)
        time_of_day_seconds = sampled_time % 86400  # Extract just the time-of-day portion
        
        base_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) \
                    - timedelta(days=random_day_offset) \
                    + timedelta(seconds=time_of_day_seconds)
        
        # 5% chance of amount mismatch (for rule engine)
        payment_amount = amount
        if random.random() < 0.05:
            payment_amount = amount + 10.0

        customer_claims = {
            "product not received": "I have been waiting for weeks and my order never arrived.",
            "product not as described": "The item I received is completely different from the pictures.",
            "duplicate charge": "I was charged twice for the same order.",
            "subscription not cancelled": "I cancelled this before the renewal date but still got charged.",
            "unauthorized transaction": "I did not make this purchase. My card was stolen."
        }
        
        db_case = Case(
            id=case_id,
            transaction_id=f"txn_{random.randint(10000, 99999)}",
            dispute_reason=category,
            customer_claim=customer_claims[category],
            merchant_id=f"merch_{random.randint(100, 999)}",
            amount=amount,
            status="new",
            created_at=base_date + timedelta(days=5) # dispute filed 5 days later
        )
        db.add(db_case)
        
        # Add basic payment evidence for almost all cases
        db.add(Evidence(
            case_id=case_id,
            evidence_type="payment",
            source_id=db_case.transaction_id,
            content={"amount": payment_amount, "currency": "INR", "status": "success"},
            event_timestamp=base_date
        ))
        
        # Add a refund before payment contradiction (5% chance)
        if random.random() < 0.05:
            db.add(Evidence(
                case_id=case_id,
                evidence_type="refund",
                content={"amount": amount, "status": "processed"},
                event_timestamp=base_date - timedelta(days=1) # Contradiction!
            ))

        # Generate category-specific evidence
        if category == "product not received":
            if label == "legitimate":
                # Merchant is right, product was delivered
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="delivery",
                    source_id=f"trk_{random.randint(1000, 9999)}",
                    content={"status": "delivered", "address_match": True, "signed_by": "Customer"},
                    event_timestamp=base_date + timedelta(days=3)
                ))
            elif label == "fraudulent":
                # Customer is right, product lost or no delivery evidence
                if random.random() > 0.5:
                    db.add(Evidence(
                        case_id=case_id,
                        evidence_type="delivery",
                        source_id=f"trk_{random.randint(1000, 9999)}",
                        content={"status": "lost_in_transit", "address_match": True},
                        event_timestamp=base_date + timedelta(days=3)
                    ))
            elif label == "ambiguous":
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="delivery",
                    source_id=f"trk_{random.randint(1000, 9999)}",
                    content={"status": "delivered", "address_match": False, "notes": "Left at front porch"},
                    event_timestamp=base_date + timedelta(days=3)
                ))
                
        elif category == "duplicate charge":
            if label == "fraudulent":
                # Actually charged twice
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="payment",
                    source_id=f"txn_{random.randint(10000, 99999)}_dup",
                    content={"amount": amount, "currency": "INR", "status": "success"},
                    event_timestamp=base_date + timedelta(minutes=2)
                ))
            elif label == "ambiguous":
                # Two charges but different amounts
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="payment",
                    source_id=f"txn_{random.randint(10000, 99999)}_diff",
                    content={"amount": amount / 2, "currency": "INR", "status": "success"},
                    event_timestamp=base_date + timedelta(minutes=5)
                ))
            # If legitimate, we do nothing (only one payment exists)

        elif category == "subscription not cancelled":
            if label == "legitimate":
                # Cancelled AFTER billing
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="communication",
                    content={"message": "Please cancel my subscription", "channel": "email"},
                    event_timestamp=base_date + timedelta(days=1) # Billed on base_date
                ))
            elif label == "fraudulent":
                # Cancelled BEFORE billing
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="communication",
                    content={"message": "Please cancel my subscription", "channel": "email"},
                    event_timestamp=base_date - timedelta(days=2) 
                ))
            elif label == "ambiguous":
                # Missing communication evidence entirely (so we can't prove either way)
                pass

        elif category == "unauthorized transaction":
            if label == "legitimate":
                # Customer verified OTP, merchant is right
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="otp",
                    content={"verified": True, "method": "sms"},
                    event_timestamp=base_date
                ))
            elif label == "fraudulent":
                # No OTP or failed OTP
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="otp",
                    content={"verified": False, "method": "sms"},
                    event_timestamp=base_date
                ))
            elif label == "ambiguous":
                # OTP verified but weird IP
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="otp",
                    content={"verified": True, "method": "sms", "ip_address": "unknown_foreign_ip"},
                    event_timestamp=base_date
                ))
                
        elif category == "product not as described":
            # Mostly relies on communication and photos which we simulate as text
            if label == "legitimate":
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="communication",
                    content={"message": "It works fine but I just don't like the color.", "channel": "chat"},
                    event_timestamp=base_date + timedelta(days=4)
                ))
            elif label == "fraudulent":
                db.add(Evidence(
                    case_id=case_id,
                    evidence_type="communication",
                    content={"message": "The screen is completely shattered and it won't turn on.", "channel": "chat", "has_attachments": True},
                    event_timestamp=base_date + timedelta(days=4)
                ))
            else:
                pass # Ambiguous, no clear communication
                
    db.commit()
    db.close()
    
    # Write ground truth to file
    gt_path = os.path.join(os.path.dirname(__file__), 'ground_truth.json')
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
        
    print(f"Successfully generated {num_cases} cases (150 dev, 30 test).")
    print(f"Ground truth labels saved to {gt_path}")

if __name__ == "__main__":
    generate_cases()
