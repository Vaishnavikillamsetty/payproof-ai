import pathlib

p = pathlib.Path('payproof-backend/app/main.py')
text = p.read_text(encoding='utf-8')

log_setup = """import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""

if "logging.basicConfig" not in text:
    text = text.replace("from fastapi import FastAPI", log_setup + "from fastapi import FastAPI")
    p.write_text(text, encoding='utf-8')
