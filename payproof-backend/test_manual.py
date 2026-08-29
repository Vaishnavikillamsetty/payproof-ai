from datetime import datetime, timedelta
from types import SimpleNamespace

from app.rules.engine import check_timeline_rules


# Helper function to create dummy evidence
def evidence(evidence_type, content, timestamp):
    return SimpleNamespace(
        evidence_type=evidence_type,
        content=content,
        event_timestamp=timestamp
    )


# Helper function to create dummy case
def case(dispute_reason, amount=100):
    return SimpleNamespace(
        dispute_reason=dispute_reason,
        amount=amount
    )


# Helper function to print results
def run_test(test_name, test_case, evidence_list):
    flags = check_timeline_rules(test_case, evidence_list)

    print("\n" + "=" * 60)
    print(test_name)
    print("=" * 60)

    if flags:
        for flag in flags:
            print(f"FLAG: {flag[0]}")
            print(f"MESSAGE: {flag[2]}")
    else:
        print("No flags triggered.")

    return flags


now = datetime.now()


# --------------------------------------------------
# 1. REFUND BEFORE PAYMENT
# --------------------------------------------------

flags = run_test(
    "TEST 1: Refund Before Payment",
    case("product not received"),
    [
        evidence(
            "payment",
            {"amount": 100},
            now
        ),
        evidence(
            "refund",
            {"amount": 100},
            now - timedelta(days=1)
        )
    ]
)

assert any(f[0] == "refund_before_payment" for f in flags)


# --------------------------------------------------
# 2. DELIVERY EXISTS BUT DISPUTED
# --------------------------------------------------

flags = run_test(
    "TEST 2: Delivery Exists But Product Not Received",
    case("product not received"),
    [
        evidence(
            "payment",
            {"amount": 100},
            now
        ),
        evidence(
            "delivery",
            {"status": "delivered"},
            now + timedelta(days=2)
        )
    ]
)

assert any(
    f[0] == "delivery_evidence_exists_but_disputed"
    for f in flags
)


# --------------------------------------------------
# 3. AMOUNT MISMATCH
# --------------------------------------------------

flags = run_test(
    "TEST 3: Amount Mismatch",
    case("product not as described", amount=100),
    [
        evidence(
            "payment",
            {"amount": 120},
            now
        )
    ]
)

assert any(f[0] == "amount_mismatch" for f in flags)


# --------------------------------------------------
# 4. UNAUTHORIZED BUT OTP VERIFIED
# --------------------------------------------------

flags = run_test(
    "TEST 4: Unauthorized Transaction But OTP Verified",
    case("unauthorized transaction"),
    [
        evidence(
            "payment",
            {"amount": 100},
            now
        ),
        evidence(
            "otp",
            {"verified": True, "method": "sms"},
            now
        )
    ]
)

assert any(
    f[0] == "unauthorized_but_otp_verified"
    for f in flags
)


# --------------------------------------------------
# 5. DUPLICATE CHARGE WITHOUT MULTIPLE PAYMENTS
# --------------------------------------------------

flags = run_test(
    "TEST 5: Duplicate Charge With Only One Payment",
    case("duplicate charge"),
    [
        evidence(
            "payment",
            {"amount": 100},
            now
        )
    ]
)

assert any(
    f[0] == "duplicate_charge_missing_evidence"
    for f in flags
)


# --------------------------------------------------
# 6. CANCELLATION WITHOUT RECORD
# --------------------------------------------------

flags = run_test(
    "TEST 6: Subscription Not Cancelled Without Record",
    case("subscription not cancelled"),
    [
        evidence(
            "payment",
            {"amount": 100},
            now
        )
    ]
)

assert any(
    f[0] == "cancellation_without_record"
    for f in flags
)


print("\n" + "=" * 60)
print("ALL 6 RULE TESTS PASSED SUCCESSFULLY!")
print("=" * 60)