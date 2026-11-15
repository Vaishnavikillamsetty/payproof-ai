import pathlib
p = pathlib.Path('payproof-backend/app/agents/investigation_agent.py')
text = p.read_text(encoding='utf-8')
text = text.replace('        print("DIAGNOSTIC - Anthropic request failed (Exception): " + str(e))', '                print("DIAGNOSTIC - Anthropic request failed (Exception): " + str(e))')
p.write_text(text, encoding='utf-8')
