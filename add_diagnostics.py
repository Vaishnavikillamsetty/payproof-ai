import pathlib

p = pathlib.Path('payproof-backend/app/agents/investigation_agent.py')
text = p.read_text(encoding='utf-8')

diagnostics = """
    # --- DIAGNOSTICS FOR RENDER ---
    import os
    env_key = os.environ.get('ANTHROPIC_API_KEY', 'NOT_SET')
    logger.info("DIAGNOSTIC - ANTHROPIC_API_KEY in os.environ: %s", "SET_AND_HIDDEN" if env_key != 'NOT_SET' and len(env_key) > 5 else env_key)
    logger.info("DIAGNOSTIC - settings.anthropic_api_key configured: %s", bool(settings.anthropic_api_key))
    logger.info("DIAGNOSTIC - settings.anthropic_model: %s", settings.anthropic_model)
    logger.info("DIAGNOSTIC - settings.mock_verifier: %s", settings.mock_verifier)
    # ------------------------------
"""

text = text.replace(
    'if not settings.anthropic_api_key:',
    diagnostics + '\n    if not settings.anthropic_api_key:'
)

text = text.replace(
    'except (json.JSONDecodeError, ValidationError) as e:',
    'except (json.JSONDecodeError, ValidationError) as e:\n        logger.error("DIAGNOSTIC - Anthropic request failed (validation): %s", e)'
)

text = text.replace(
    'except anthropic.APIError as e:',
    'except anthropic.APIError as e:\n        logger.error("DIAGNOSTIC - Anthropic request failed (API Error): %s", e)'
)

text = text.replace(
    'except Exception as e:',
    'except Exception as e:\n        logger.error("DIAGNOSTIC - Anthropic request failed (Exception): %s", e)'
)

text = text.replace(
    'logger.info("Starting Anthropic investigation agent for case %s", case_id)',
    'logger.info("DIAGNOSTIC - Starting Anthropic investigation agent for case %s", case_id)'
)

p.write_text(text, encoding='utf-8')
