import pathlib
import re

p = pathlib.Path('app/routers/cases.py')
text = p.read_text(encoding='utf-8')

text = text.replace(
    'demo_amount = get_demo_expected_amount(db, case_in.transaction_id)',
    """demo_amount = get_demo_expected_amount(db, case_in.transaction_id)
    
    # Try to fetch currency from db
    from app.db.models import PaymentGatewayRecord
    from app.agents.external_systems import _get_base_demo_id
    base_id = _get_base_demo_id(case_in.transaction_id)
    pmt = db.query(PaymentGatewayRecord).filter_by(transaction_id=base_id).first()
    final_currency = pmt.currency if pmt else "USD\""""
)

# Replace the db_case creation
old_db_case = """db_case = Case(
        transaction_id=case_in.transaction_id,
        dispute_reason=case_in.dispute_reason,
        customer_claim=case_in.customer_claim,
        merchant_id=case_in.merchant_id,
        amount=final_amount,
        status="new",
    )"""
new_db_case = """db_case = Case(
        transaction_id=case_in.transaction_id,
        dispute_reason=case_in.dispute_reason,
        customer_claim=case_in.customer_claim,
        merchant_id=case_in.merchant_id,
        amount=final_amount,
        currency=final_currency,
        status="new",
    )"""
text = text.replace(old_db_case, new_db_case)

# Update human review endpoint to preserve AI recommendation
old_review = """    if req.action == "escalate":
        case.status = "escalate"
    elif req.action == "request_more_evidence":
        case.status = "request_more_evidence"
    elif req.action == "approve":
        case.status = "resolved\""""
new_review = """    if req.action == "escalate":
        case.final_action = "escalate"
    elif req.action == "request_more_evidence":
        case.final_action = "request_more_evidence"
    elif req.action == "approve":
        case.final_action = case.ai_recommendation
        
    case.status = "resolved\""""
text = text.replace(old_review, new_review)

p.write_text(text, encoding='utf-8')
