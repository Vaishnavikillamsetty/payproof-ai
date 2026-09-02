"""
Normalized internal data models for the Razorpay provider abstraction layer.

AMOUNT REPRESENTATION (IMPORTANT):
All amounts across the system are stored as integers in the MINOR UNIT
of the currency (paise for INR, cents for USD).

Examples:
  ₹299.99  → amount_minor=29999,  currency="INR"
  $150.00  → amount_minor=15000,  currency="USD"

This avoids floating-point precision issues in financial comparisons.
Any display conversion (minor → major units) happens only at the API
response or frontend layer, never inside business logic.
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class NormalizedPaymentDetails(BaseModel):
    payment_id: str
    amount_minor: int       # e.g. 29999 for ₹299.99 or $299.99
    currency: str           # ISO 4217: "INR", "USD"
    status: str
    order_id: Optional[str] = None
    created_at: datetime
    source: str             # "LIVE_RAZORPAY_API" or "DEMO_RAZORPAY_DATA"
    mode: str               # "live" or "demo"


class NormalizedDisputeDetails(BaseModel):
    dispute_id: str
    payment_id: str
    amount_minor: int
    currency: str
    reason_code: str
    reason_description: str
    status: str
    phase: str
    created_at: datetime
    source: str
    mode: str


class NormalizedRefundDetails(BaseModel):
    refund_id: str
    payment_id: str
    amount_minor: int
    currency: str
    status: str
    created_at: datetime
    source: str
    mode: str
