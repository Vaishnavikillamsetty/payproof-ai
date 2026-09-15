from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/payproof"
    # OpenRouter (replaces Anthropic)
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    # Legacy Anthropic fields kept as empty strings so nothing else breaks
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    internal_admin_token: str = "dev_admin_token"
    mock_verifier: bool = True
    
    environment: str = "development"
    demo_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
