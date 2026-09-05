import pathlib

p = pathlib.Path('src/components/AgentActivity.tsx')
text = p.read_text(encoding='utf-8')

# Fix text about rule based fallback
old_mock_text = "Rule-based investigation pipeline used for this demonstration. No live LLM call was made."
new_mock_text = "Deterministic safety analysis used because live AI verification is unavailable."
text = text.replace(old_mock_text, new_mock_text)

# Also fix the emojis I see in the file
text = text.replace('dY -', '🤖')
text = text.replace('s', '⚠')
text = text.replace('o"', '✓')

p.write_text(text, encoding='utf-8')
