import hmac
import hashlib
import logging
from typing import List, Optional
from datetime import datetime, timezone
import httpx
import os

from app.services.razorpay.base import RazorpayProvider
from app.services.razorpay.models import (
    NormalizedPaymentDetails,
    NormalizedDisputeDetails,
    NormalizedRefundDetails
)

logger = logging.getLogger(__name__)


class LiveRazorpayProvider(RazorpayProvider):
    """
    Live provider that makes real HTTP calls to the Razorpay API.
    Credentials loaded exclusively from environment variables.
    All amounts are returned as integer minor units (paise for INR).
    """

    SOURCE = "LIVE_RAZORPAY_API"
    MODE = "live"
    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.key_id = os.environ.get("RAZORPAY_KEY_ID")
        self.key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
        self.webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET")

        if not self.key_id or not self.key_secret:
            raise ValueError(
                "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in environment for live mode."
            )

        # Never log the actual key values
        logger.info("LiveRazorpayProvider initialized with key_id=rzp_***")
        self.auth = (self.key_id, self.key_secret)
        self.client = httpx.Client(auth=self.auth, timeout=10.0)

    def get_payment_details(self, payment_id: str) -> Optional[NormalizedPaymentDetails]:
        try:
            response = self.client.get(f"{self.BASE_URL}/payments/{payment_id}")
            response.raise_for_status()
            data = response.json()

            return NormalizedPaymentDetails(
                payment_id=data["id"],
                amount_minor=int(data.get("amount", 0)),  # Razorpay returns integer paise
                currency=data.get("currency", "INR"),
                status=data.get("status", "unknown"),
                order_id=data.get("order_id"),
                created_at=datetime.fromtimestamp(data.get("created_at", 0), timezone.utc),
                source=self.SOURCE,
                mode=self.MODE
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error("HTTP error fetching payment %s: status=%d", payment_id, e.response.status_code)
            raise
        except Exception as e:
            logger.error("Network error fetching payment %s: %s", payment_id, type(e).__name__)
            raise

    def get_refund_details(self, payment_id: str) -> List[NormalizedRefundDetails]:
        try:
            response = self.client.get(f"{self.BASE_URL}/payments/{payment_id}/refunds")
            response.raise_for_status()
            data = response.json()

            return [
                NormalizedRefundDetails(
                    refund_id=item["id"],
                    payment_id=payment_id,
                    amount_minor=int(item.get("amount", 0)),
                    currency=item.get("currency", "INR"),
                    status=item.get("status", "unknown"),
                    created_at=datetime.fromtimestamp(item.get("created_at", 0), timezone.utc),
                    source=self.SOURCE,
                    mode=self.MODE
                )
                for item in data.get("items", [])
            ]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            logger.error("HTTP error fetching refunds for %s: status=%d", payment_id, e.response.status_code)
            raise
        except Exception as e:
            logger.error("Network error fetching refunds %s: %s", payment_id, type(e).__name__)
            raise

    def get_dispute_details(self, dispute_id: str) -> Optional[NormalizedDisputeDetails]:
        try:
            response = self.client.get(f"{self.BASE_URL}/disputes/{dispute_id}")
            response.raise_for_status()
            data = response.json()

            return NormalizedDisputeDetails(
                dispute_id=data["id"],
                payment_id=data.get("payment_id", ""),
                amount_minor=int(data.get("amount", 0)),
                currency=data.get("currency", "INR"),
                reason_code=data.get("reason_code", "unknown"),
                reason_description=data.get("reason_description", "unknown"),
                status=data.get("status", "open"),
                phase=data.get("phase", "fraud"),
                created_at=datetime.fromtimestamp(data.get("created_at", 0), timezone.utc),
                source=self.SOURCE,
                mode=self.MODE
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error("HTTP error fetching dispute %s: status=%d", dispute_id, e.response.status_code)
            raise
        except Exception as e:
            logger.error("Network error fetching dispute %s: %s", dispute_id, type(e).__name__)
            raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify X-Razorpay-Signature using HMAC-SHA256.
        IMPORTANT: payload must be the raw, unmodified request body bytes —
        never JSON-parsed and re-serialized, as that would change whitespace
        and break the HMAC comparison.
        """
        if not self.webhook_secret:
            logger.error("RAZORPAY_WEBHOOK_SECRET is not configured — cannot verify webhook.")
            return False

        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)
