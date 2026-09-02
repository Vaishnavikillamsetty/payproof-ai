import hmac
import hashlib
import logging
from typing import List, Optional
from datetime import datetime, timezone
import httpx

from app.services.razorpay.base import RazorpayProvider
from app.services.razorpay.models import (
    NormalizedPaymentDetails,
    NormalizedDisputeDetails,
    NormalizedRefundDetails
)
import os

logger = logging.getLogger(__name__)

class LiveRazorpayProvider(RazorpayProvider):
    """
    Live provider that makes real HTTP calls to the Razorpay API.
    """
    
    SOURCE = "LIVE_RAZORPAY_API"
    MODE = "live"
    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.key_id = os.environ.get("RAZORPAY_KEY_ID")
        self.key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
        self.webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET")

        if not self.key_id or not self.key_secret:
            raise ValueError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in live mode.")

        self.auth = (self.key_id, self.key_secret)
        self.client = httpx.Client(auth=self.auth, timeout=10.0)

    def get_payment_details(self, payment_id: str) -> Optional[NormalizedPaymentDetails]:
        try:
            response = self.client.get(f"{self.BASE_URL}/payments/{payment_id}")
            response.raise_for_status()
            data = response.json()
            
            return NormalizedPaymentDetails(
                payment_id=data.get("id"),
                amount=data.get("amount", 0) / 100.0, # Razorpay amounts are in paise
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
            logger.error(f"HTTP error fetching payment details: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Network error fetching payment details: {e}")
            raise

    def get_refund_details(self, payment_id: str) -> List[NormalizedRefundDetails]:
        try:
            response = self.client.get(f"{self.BASE_URL}/payments/{payment_id}/refunds")
            response.raise_for_status()
            data = response.json()
            
            refunds = []
            for item in data.get("items", []):
                refunds.append(NormalizedRefundDetails(
                    refund_id=item.get("id"),
                    payment_id=payment_id,
                    amount=item.get("amount", 0) / 100.0,
                    currency=item.get("currency", "INR"),
                    status=item.get("status", "unknown"),
                    created_at=datetime.fromtimestamp(item.get("created_at", 0), timezone.utc),
                    source=self.SOURCE,
                    mode=self.MODE
                ))
            return refunds
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            logger.error(f"HTTP error fetching refunds: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Network error fetching refunds: {e}")
            raise

    def get_dispute_details(self, dispute_id: str) -> Optional[NormalizedDisputeDetails]:
        try:
            response = self.client.get(f"{self.BASE_URL}/disputes/{dispute_id}")
            response.raise_for_status()
            data = response.json()
            
            return NormalizedDisputeDetails(
                dispute_id=data.get("id"),
                payment_id=data.get("payment_id"),
                amount=data.get("amount", 0) / 100.0,
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
            logger.error(f"HTTP error fetching dispute: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Network error fetching dispute: {e}")
            raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            logger.error("RAZORPAY_WEBHOOK_SECRET is not configured.")
            return False
            
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
