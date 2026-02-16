"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+psycopg://sibyl:sibyl@db:5432/sibyl"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # OpenRouter
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Application
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_JUDGE_ITERATIONS: int = 3
    AUTO_START_ANALYSIS: bool = False  # Set True for demo mode to auto-trigger claims extraction

    # Tavily Search API (for News/Media and Academic agents)
    TAVILY_API_KEY: str | None = None
    SEARCH_MAX_RESULTS: int = 10
    SEARCH_TIMEOUT_SECONDS: int = 30


# Singleton settings instance
settings = Settings()
