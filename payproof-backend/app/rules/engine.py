import math


def check_timeline_rules(case, evidence_list):
    flags = []

    # Get specific evidence types
    payment_evts = [e for e in evidence_list if e.evidence_type == "payment"]
    payment_evt = payment_evts[0] if payment_evts else None

    delivery_evt = next((e for e in evidence_list if e.evidence_type == "delivery"), None)
    refund_evt = next((e for e in evidence_list if e.evidence_type == "refund"), None)
    otp_evts = [e for e in evidence_list if e.evidence_type == "otp"]
    otp_evt = otp_evts[0] if otp_evts else None
    communication_evt = next((e for e in evidence_list if e.evidence_type == "communication"), None)

    # 1. Refund before payment
    if refund_evt and payment_evt and refund_evt.event_timestamp and payment_evt.event_timestamp:
        if refund_evt.event_timestamp < payment_evt.event_timestamp:
            flags.append(("refund_before_payment", True, "Refund timestamp precedes payment timestamp"))

    # 2. Delivery evidence exists but disputed
    if (
        case.dispute_reason == "product not received"
        and delivery_evt is not None
        and delivery_evt.content.get("status") == "delivered"
    ):
        flags.append(("delivery_evidence_exists_but_disputed", True,
                       "Delivery record shows delivered despite non-receipt claim — needs verifier review"))

    # 3. Amount mismatch — use a ₹0.01 tolerance to avoid spurious flags from
    #    floating-point representation differences (e.g. 299.99 vs 299.9900000001).
    #    A genuine mismatch (e.g. case.amount=0 vs payment=299.99) will still fire.
    if payment_evt:
        payment_amount = payment_evt.content.get("amount")
        if payment_amount is not None:
            case_amt = float(case.amount)
            pay_amt = float(payment_amount)
            if not math.isclose(case_amt, pay_amt, abs_tol=0.01):
                flags.append(("amount_mismatch", True,
                               f"Disputed amount ({case.amount}) does not match payment record ({payment_amount})"))

    # 4. Conflicting authentication evidence is a security signal. It must
    # take precedence over a single successful OTP record or generic evidence
    # completeness when producing the deterministic recommendation.
    otp_verified_values = {e.content.get("verified") for e in otp_evts if e.content.get("verified") in (True, False)}
    if otp_verified_values == {True, False}:
        flags.append(("conflicting_otp_verification", True,
                      "Authentication records conflict: both verified and unverified OTP events were found"))

    # 5. Unauthorized transaction but OTP verified
    if case.dispute_reason == "unauthorized transaction" and otp_evt is not None:
        if otp_evt.content.get("verified") is True:
            flags.append(("unauthorized_but_otp_verified", True,
                           "Transaction is disputed as unauthorized but OTP verification succeeded"))

    # 6. Duplicate charge without multiple payments
    if case.dispute_reason == "duplicate charge":
        if len(payment_evts) < 2:
            flags.append(("duplicate_charge_missing_evidence", True,
                           "Claim is duplicate charge but multiple payment records were not found"))

    # 7. Cancellation claim but no communication/cancellation record
    if case.dispute_reason == "subscription not cancelled":
        # Check if there is any communication evidence showing cancellation
        has_cancellation = False
        if communication_evt and "cancel" in str(communication_evt.content.get("message", "")).lower():
            has_cancellation = True

        if not has_cancellation:
             flags.append(("cancellation_without_record", True,
                            "Claim is subscription not cancelled but no cancellation communication found"))

    return flags
