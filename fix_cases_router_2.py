import pathlib
p = pathlib.Path('payproof-backend/app/routers/cases.py')
text = p.read_text(encoding='utf-8')
text = text.replace(
    'background_tasks.add_task(run_pipeline, db_case.id)',
    'print(f"DIAGNOSTIC - STARTING BACKGROUND INVESTIGATION for {db_case.id}")\n    background_tasks.add_task(run_pipeline, db_case.id)'
)
p.write_text(text, encoding='utf-8')
