import hashlib
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import PaymentGatewayRecord
from app.services.razorpay.base import RazorpayProvider
from app.services.razorpay.models import (
    NormalizedPaymentDetails,
    NormalizedDisputeDetails,
    NormalizedRefundDetails
)

def _hash_scenario(txn_id: str) -> int:
    digest = hashlib.sha256(txn_id.encode()).hexdigest()
    return int(digest[:8], 16) % 10

class DemoRazorpayProvider(RazorpayProvider):
    """
    Demo provider for the Razorpay Buildathon.
    Uses seeded database tables or deterministic generation to simulate the Razorpay API.
    """
    
    SOURCE = "DEMO_RAZORPAY_DATA"
    MODE = "demo"

    def _get_db(self) -> Session:
        return SessionLocal()

    def get_payment_details(self, payment_id: str) -> Optional[NormalizedPaymentDetails]:
        db = self._get_db()
        try:
            # Check seeded data first
            rec = db.query(PaymentGatewayRecord).filter_by(transaction_id=payment_id).first()
            if rec:
                return NormalizedPaymentDetails(
                    payment_id=payment_id,
                    amount=float(rec.amount),
                    currency=rec.currency,
                    status=rec.status,
                    created_at=rec.timestamp or datetime.now(timezone.utc),
                    source=self.SOURCE,
                    mode=self.MODE
                )
            
            # Deterministic fallback for unseeded IDs
            if payment_id.startswith("DEMO_TXN_EMPTY"):
                return None
                
            bucket = _hash_scenario(payment_id)
            if bucket <= 8:
                return NormalizedPaymentDetails(
                    payment_id=payment_id,
                    amount=299.99, # Arbitrary default for unseeded generated
                    currency="USD",
                    status="captured",
                    created_at=datetime.now(timezone.utc),
                    source=self.SOURCE,
                    mode=self.MODE
                )
            return None
        finally:
            db.close()

    def get_refund_details(self, payment_id: str) -> List[NormalizedRefundDetails]:
        bucket = _hash_scenario(payment_id)
        # Simulate a refund for specific hash buckets if requested in a demo
        if bucket == 7: # Example arbitrary bucket for refunds
            return [NormalizedRefundDetails(
                refund_id=f"rfnd_{payment_id[-6:]}",
                payment_id=payment_id,
                amount=299.99,
                currency="USD",
                status="processed",
                created_at=datetime.now(timezone.utc),
                source=self.SOURCE,
                mode=self.MODE
            )]
        return []

    def get_dispute_details(self, dispute_id: str) -> Optional[NormalizedDisputeDetails]:
        # Generate a stable fake dispute
        return NormalizedDisputeDetails(
            dispute_id=dispute_id,
            payment_id=f"pay_{dispute_id[-6:]}",
            amount=299.99,
            currency="USD",
            reason_code="product_not_received",
            reason_description="Customer claims product was not delivered",
            status="open",
            phase="chargeback",
            created_at=datetime.now(timezone.utc),
            source=self.SOURCE,
            mode=self.MODE
        )

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        # In demo mode, always accept for ease of testing, or enforce a static test signature
        if signature == "test_demo_signature":
            return True
        return False
