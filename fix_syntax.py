import pathlib
p = pathlib.Path('payproof-backend/app/agents/investigation_agent.py')
text = p.read_text(encoding='utf-8')

# The bad line:
# print("DIAGNOSTIC - ANTHROPIC_API_KEY in os.environ: " + str("SET_AND_HIDDEN" if env_key != 'NOT_SET' and len(env_key)) > 5 else env_key)
# We need it to be:
# print("DIAGNOSTIC - ANTHROPIC_API_KEY in os.environ: " + str("SET_AND_HIDDEN" if env_key != 'NOT_SET' and len(env_key) > 5 else env_key))

text = text.replace(
    'print("DIAGNOSTIC - ANTHROPIC_API_KEY in os.environ: " + str("SET_AND_HIDDEN" if env_key != \'NOT_SET\' and len(env_key)) > 5 else env_key)',
    'print("DIAGNOSTIC - ANTHROPIC_API_KEY in os.environ: " + str("SET_AND_HIDDEN" if env_key != \'NOT_SET\' and len(env_key) > 5 else env_key))'
)
p.write_text(text, encoding='utf-8')
