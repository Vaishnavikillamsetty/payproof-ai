import pathlib
p = pathlib.Path('payproof-backend/app/agents/investigation_agent.py')
text = p.read_text(encoding='utf-8')
text = text.replace('                print("DIAGNOSTIC - Anthropic request failed (Exception): " + str(e))\n        logger.error("Agent failed for case', '        print("DIAGNOSTIC - Anthropic request failed (Exception): " + str(e))\n        logger.error("Agent failed for case')
p.write_text(text, encoding='utf-8')
