import pathlib
p = pathlib.Path('payproof-backend/app/routers/cases.py')
text = p.read_text(encoding='utf-8')

replacement = """def create_case(
    case_in: CaseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    print(f"DIAGNOSTIC - CASE CREATE POST RECEIVED for tx: {case_in.transaction_id}")
    \"\"\"
    Submit a new dispute.
    \"\"\""""

text = text.replace("""def create_case(
    case_in: CaseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    \"\"\"
    Submit a new dispute.
    \"\"\"""", replacement)

p.write_text(text, encoding='utf-8')
