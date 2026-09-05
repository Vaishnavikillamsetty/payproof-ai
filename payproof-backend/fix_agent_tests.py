import pathlib
import re

p = pathlib.Path('tests/test_investigation_agent.py')
text = p.read_text(encoding='utf-8')

# Ensure we import settings
if 'from app.config import settings' not in text:
    text = text.replace('from app.agents.investigation_agent import', 'from app.config import settings\nfrom app.agents.investigation_agent import')

# Add a fixture to clear the API key
fixture = """
@pytest.fixture(autouse=True)
def disable_real_llm():
    old_key = settings.anthropic_api_key
    settings.anthropic_api_key = ""
    yield
    settings.anthropic_api_key = old_key
"""

if 'def disable_real_llm' not in text:
    text = text.replace('# --------------------------------------------------------------------------- #\n# Schema Validation Tests', fixture + '\n# --------------------------------------------------------------------------- #\n# Schema Validation Tests')

p.write_text(text, encoding='utf-8')
