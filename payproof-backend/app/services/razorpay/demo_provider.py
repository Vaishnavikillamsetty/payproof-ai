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

    Uses seeded database tables or deterministic generation to simulate
    the Razorpay API. All amounts are in minor units (paise/cents).
    Clearly labelled as DEMO_RAZORPAY_DATA so the UI can distinguish
    demo data from live Razorpay data.
    """

    SOURCE = "DEMO_RAZORPAY_DATA"
    MODE = "demo"

    def _get_db(self) -> Session:
        return SessionLocal()

    def get_payment_details(self, payment_id: str) -> Optional[NormalizedPaymentDetails]:
        db = self._get_db()
        try:
            rec = db.query(PaymentGatewayRecord).filter_by(transaction_id=payment_id).first()
            if rec:
                # Convert decimal to integer minor units (multiply by 100)
                amount_minor = int(round(float(rec.amount) * 100))
                return NormalizedPaymentDetails(
                    payment_id=payment_id,
                    amount_minor=amount_minor,
                    currency=rec.currency,
                    status=rec.status,
                    created_at=rec.timestamp or datetime.now(timezone.utc),
                    source=self.SOURCE,
                    mode=self.MODE
                )

            # Known intentionally empty IDs — never fallback
            if payment_id.startswith("DEMO_TXN_EMPTY"):
                return None

            # Deterministic hash fallback for unseeded non-DEMO_ IDs
            bucket = _hash_scenario(payment_id)
            if bucket <= 8:
                return NormalizedPaymentDetails(
                    payment_id=payment_id,
                    amount_minor=29999,  # $299.99 in cents
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
        if bucket == 7:
            return [NormalizedRefundDetails(
                refund_id=f"rfnd_{payment_id[-6:]}",
                payment_id=payment_id,
                amount_minor=29999,
                currency="USD",
                status="processed",
                created_at=datetime.now(timezone.utc),
                source=self.SOURCE,
                mode=self.MODE
            )]
        return []

    def get_dispute_details(self, dispute_id: str) -> Optional[NormalizedDisputeDetails]:
        return NormalizedDisputeDetails(
            dispute_id=dispute_id,
            payment_id=f"pay_{dispute_id[-6:]}",
            amount_minor=29999,
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
        """
        In demo mode, accept the static test signature string.
        The real HMAC-SHA256 verification lives in LiveRazorpayProvider.
        NOTE: payload must be the raw request bytes — never JSON-parsed/re-serialized.
        """
        if signature == "test_demo_signature":
            return True
        return False
