from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class NormalizedPaymentDetails(BaseModel):
    payment_id: str
    amount: float
    currency: str
    status: str
    order_id: Optional[str] = None
    created_at: datetime
    source: str
    mode: str

class NormalizedDisputeDetails(BaseModel):
    dispute_id: str
    payment_id: str
    amount: float
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
    amount: float
    currency: str
    status: str
    created_at: datetime
    source: str
    mode: str
