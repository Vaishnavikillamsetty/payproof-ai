with open('app/routers/cases.py', 'a', encoding='utf-8') as f:
    f.write("""
@router.delete("/demo-reset")
def reset_demo_cases(db: Session = Depends(get_db)):
    \"\"\"
    Deletes all dynamically generated demo cases to provide a clean state.
    Does not delete real production cases.
    \"\"\"
    demo_cases = db.query(Case).filter(
        (Case.transaction_id.like("DEMO_TXN_%")) | 
        (Case.transaction_id.like("DEMO_SCN_%"))
    ).all()
    
    count = len(demo_cases)
    for c in demo_cases:
        db.query(AuditLog).filter(AuditLog.case_id == c.id).delete(synchronize_session=False)
        db.query(Evidence).filter(Evidence.case_id == c.id).delete(synchronize_session=False)
        # Note: the rules related models might also need deletion if they reference Case
        # Wait, the models actually don't have cascade delete enabled for some relations?
        # Let's delete the rule flags too.
        from app.db.models import RuleFlag
        db.query(RuleFlag).filter(RuleFlag.case_id == c.id).delete(synchronize_session=False)
        from app.db.models import Claim
        db.query(Claim).filter(Claim.case_id == c.id).delete(synchronize_session=False)
        db.delete(c)
    
    db.commit()
    return {"status": "success", "deleted": count}
""")
