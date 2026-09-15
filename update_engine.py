import pathlib

p = pathlib.Path('payproof-backend/app/rules/engine.py')
text = p.read_text(encoding='utf-8')

rule_to_add = """
    # 5. Duplicate Payment
    if case.dispute_reason == "duplicate_charge":
        successful_payments = [e for e in payment_evts if e.content.get("status") == "success"]
        if len(successful_payments) > 1:
            flags.append(("duplicate_payment_detected", True, "Multiple successful payment records found for this duplicate charge claim"))
"""

if "duplicate_payment_detected" not in text:
    text = text.replace('    return flags', rule_to_add + '\n    return flags')
    p.write_text(text, encoding='utf-8')
