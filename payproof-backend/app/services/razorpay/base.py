from abc import ABC, abstractmethod
from typing import List, Optional
from app.services.razorpay.models import (
    NormalizedPaymentDetails,
    NormalizedDisputeDetails,
    NormalizedRefundDetails
)

class RazorpayProvider(ABC):
    """Abstract interface for Razorpay capabilities."""

    @abstractmethod
    def get_payment_details(self, payment_id: str) -> Optional[NormalizedPaymentDetails]:
        """Fetch payment details by ID."""
        pass

    @abstractmethod
    def get_refund_details(self, payment_id: str) -> List[NormalizedRefundDetails]:
        """Fetch all refunds associated with a payment."""
        pass

    @abstractmethod
    def get_dispute_details(self, dispute_id: str) -> Optional[NormalizedDisputeDetails]:
        """Fetch details of a specific dispute."""
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the X-Razorpay-Signature for incoming webhooks."""
        pass

    # External actions like contest_dispute will be added later in the Action Service layer,
    # keeping them out of the read-only AI investigation context for safety.
