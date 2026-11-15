import pathlib
import re

p = pathlib.Path('payproof-backend/app/agents/investigation_agent.py')
text = p.read_text(encoding='utf-8')

text = text.replace('logger.info("DIAGNOSTIC', 'print("DIAGNOSTIC')
text = text.replace('logger.error("DIAGNOSTIC', 'print("DIAGNOSTIC')

# Fix the print statements replacing logger calls that had comma formatting
text = re.sub(r'print\("DIAGNOSTIC - ANTHROPIC_API_KEY in os\.environ: %s", (.*?)\)', r'print("DIAGNOSTIC - ANTHROPIC_API_KEY in os.environ: " + str(\1))', text)
text = re.sub(r'print\("DIAGNOSTIC - settings\.anthropic_api_key configured: %s", bool\((.*?)\)\)', r'print("DIAGNOSTIC - settings.anthropic_api_key configured: " + str(bool(\1)))', text)
text = re.sub(r'print\("DIAGNOSTIC - settings\.anthropic_model: %s", (.*?)\)', r'print("DIAGNOSTIC - settings.anthropic_model: " + str(\1))', text)
text = re.sub(r'print\("DIAGNOSTIC - settings\.mock_verifier: %s", (.*?)\)', r'print("DIAGNOSTIC - settings.mock_verifier: " + str(\1))', text)
text = re.sub(r'print\("DIAGNOSTIC - Starting Anthropic investigation agent for case %s", (.*?)\)', r'print("DIAGNOSTIC - Starting Anthropic investigation agent for case " + str(\1))', text)

text = re.sub(r'print\("DIAGNOSTIC - Anthropic request failed \(validation\): %s", (.*?)\)', r'print("DIAGNOSTIC - Anthropic request failed (validation): " + str(\1))', text)
text = re.sub(r'print\("DIAGNOSTIC - Anthropic request failed \(API Error\): %s", (.*?)\)', r'print("DIAGNOSTIC - Anthropic request failed (API Error): " + str(\1))', text)
text = re.sub(r'print\("DIAGNOSTIC - Anthropic request failed \(Exception\): %s", (.*?)\)', r'print("DIAGNOSTIC - Anthropic request failed (Exception): " + str(\1))', text)

p.write_text(text, encoding='utf-8')
