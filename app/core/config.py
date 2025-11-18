"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = "Scoring API"
    app_version: str = "0.1.0"
    debug: bool = False

    # API settings
    api_prefix: str = ""

    # Scoring thresholds
    min_score: int = 300
    max_score: int = 850
    approval_threshold: int = 650

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
