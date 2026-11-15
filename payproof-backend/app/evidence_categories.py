"""
Canonical evidence category taxonomy and evidence evaluation.

Four canonical categories:
  1. TRANSACTION: Payment gateway records, refund status, transaction timestamps, amounts
  2. CUSTOMER: Customer communications, customer details, OTP/authentication logs
  3. DELIVERY: Delivery confirmations, tracking info, proof of receipt, carrier status
  4. MERCHANT: Refund policies, merchant notes, invoices, receipts, business records

CRITICAL RULE:
  Never automatically map unknown evidence types to MERCHANT.
  Unknown evidence types remain UNCATEGORIZED (None) until explicitly classified.
"""

from typing import Any, List, Optional, Set, Tuple

CANONICAL_CATEGORIES = {
    "transaction": "Transaction Evidence",
    "customer": "Customer Evidence",
    "delivery": "Delivery / Fulfilment Evidence",
    "merchant": "Merchant Evidence",
}

_TYPE_TO_CATEGORY = {
    # 1. TRANSACTION
    "payment": "transaction",
    "refund": "transaction",
    "gateway": "transaction",
    "charge": "transaction",
    "transaction": "transaction",
    "ext_payment_gateway": "transaction",
    
    # 2. CUSTOMER
    "communication": "customer",
    "customer_communication": "customer",
    "customer": "customer",
    "otp": "customer",
    "auth": "customer",
    "authentication": "customer",
    "ext_otp_log": "customer",
    "ext_communication_log": "customer",

    # 3. DELIVERY
    "delivery": "delivery",
    "tracking": "delivery",
    "fulfillment": "delivery",
    "fulfilment": "delivery",
    "shipping": "delivery",
    "proof_of_receipt": "delivery",
    "ext_delivery": "delivery",

    # 4. MERCHANT
    "merchant": "merchant",
    "merchant_communication": "merchant",
    "policy": "merchant",
    "refund_policy": "merchant",
    "invoice": "merchant",
    "receipt": "merchant",
    "merchant_notes": "merchant",
    "business_record": "merchant",
}


def map_to_canonical_category(
    evidence_type: Optional[str],
    category_override: Optional[str] = None
) -> Optional[str]:
    """
    Map an evidence type to one of the 4 canonical categories.
    If an explicit valid category_override is provided, use it.
    If evidence_type is unknown, return None (UNCATEGORIZED).
    NEVER default unknown types to 'merchant'.
    """
    if category_override:
        norm_override = category_override.strip().lower()
        if norm_override in CANONICAL_CATEGORIES:
            return norm_override
        if norm_override in ("uncategorized", "none", ""):
            return None

    if not evidence_type:
        return None

    norm_type = evidence_type.strip().lower()
    return _TYPE_TO_CATEGORY.get(norm_type, None)


def compute_category_coverage(evidence_list: List[Any]) -> Tuple[List[str], int]:
    """
    Given a list of Evidence rows or dicts:
    - Identifies which of the 4 canonical categories are represented by actual valid records.
    - Counts each category only once regardless of how many files/records belong to it.
    - Excludes uncategorized / invalid records.
    - Returns (sorted list of available categories, count out of 4).
    """
    present_categories: Set[str] = set()

    for item in evidence_list:
        # Support ORM model attributes or dictionary keys
        cat = getattr(item, "category", None) or (item.get("category") if isinstance(item, dict) else None)
        ev_type = getattr(item, "evidence_type", None) or (item.get("evidence_type") if isinstance(item, dict) else None)

        canonical = map_to_canonical_category(ev_type, category_override=cat)
        if canonical and canonical in CANONICAL_CATEGORIES:
            present_categories.add(canonical)

    # Order consistently: transaction, customer, delivery, merchant
    ordered = [c for c in ("transaction", "customer", "delivery", "merchant") if c in present_categories]
    return ordered, len(ordered)


def evaluate_evidence_strength(
    evidence_list: List[Any],
    categories_present: Optional[List[str]] = None,
    contradictions_found: bool = False,
) -> str:
    """
    Evaluate evidence strength independently from category count.
    
    Evaluates:
      - Actual evidence quality, relevance, completeness, and verification status.
      - Never equates 2/4 categories automatically with 50% strength.
      - If no evidence exists, returns "NOT_EVALUATED".
      - If contradictions exist, strength is capped at MEDIUM or LOW.
    """
    if not evidence_list:
        return "NOT_EVALUATED"

    if categories_present is None:
        categories_present, _ = compute_category_coverage(evidence_list)

    if not categories_present:
        return "NOT_EVALUATED"

    # Analyze verification status
    has_verified_payment = False
    has_confirmed_delivery = False
    has_verified_otp = False
    has_contradictory_otp = False

    for item in evidence_list:
        ev_type = (getattr(item, "evidence_type", "") or (item.get("evidence_type") if isinstance(item, dict) else "")).lower()
        content = getattr(item, "content", None) or (item.get("content") if isinstance(item, dict) else {}) or {}

        if ev_type in ("payment", "transaction"):
            status = str(content.get("status", "")).lower()
            if status in ("success", "captured", "paid", "settled"):
                has_verified_payment = True

        if ev_type in ("delivery", "fulfillment"):
            status = str(content.get("status", "")).lower()
            signed = bool(content.get("signed_by"))
            if status in ("delivered", "signed") or signed:
                has_confirmed_delivery = True

        if ev_type in ("otp", "auth"):
            verified = content.get("verified")
            if verified is True:
                has_verified_otp = True
            elif verified is False:
                has_contradictory_otp = True

    if has_verified_otp and has_contradictory_otp:
        contradictions_found = True

    # High strength requires:
    # 1. No contradictions
    # 2. Payment verified
    # 3. Delivery confirmed OR (OTP verified + customer comms)
    # 4. At least 3 categories, or solid 2 categories with confirmed delivery
    if not contradictions_found and has_verified_payment:
        if has_confirmed_delivery and ("customer" in categories_present or len(categories_present) >= 3):
            return "HIGH"
        if has_confirmed_delivery:
            return "HIGH"
        if has_verified_otp and "customer" in categories_present and len(categories_present) >= 2:
            return "MEDIUM"

    if contradictions_found:
        return "LOW" if len(categories_present) <= 2 else "MEDIUM"

    if len(categories_present) >= 2:
        return "MEDIUM"

    return "LOW"
