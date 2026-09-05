import pytest
from app.config import settings

@pytest.fixture(autouse=True)
def disable_real_llm_for_tests():
    old_key = settings.anthropic_api_key
    settings.anthropic_api_key = ""
    yield
    settings.anthropic_api_key = old_key
