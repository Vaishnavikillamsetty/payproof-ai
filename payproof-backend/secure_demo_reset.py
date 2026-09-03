import pathlib
p = pathlib.Path('app/routers/cases.py')
text = p.read_text(encoding='utf-8')

if 'from app.config import settings' not in text:
    text = text.replace('from app.schemas import', 'from app.config import settings\nfrom app.schemas import')

old_func = """@router.delete("/demo-reset")
def reset_demo_cases(db: Session = Depends(get_db)):
    \"\"\"
    Deletes all dynamically generated demo cases to provide a clean state.
    Does not delete real production cases.
    \"\"\""""

new_func = """@router.delete("/demo-reset")
def reset_demo_cases(db: Session = Depends(get_db)):
    \"\"\"
    Deletes all dynamically generated demo cases to provide a clean state.
    Does not delete real production cases.
    \"\"\"
    if settings.environment != "development" and not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Demo reset is disabled in this environment.")"""

text = text.replace(old_func, new_func)
p.write_text(text, encoding='utf-8')
print("Successfully modified cases.py")
