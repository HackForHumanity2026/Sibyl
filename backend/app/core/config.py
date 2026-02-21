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

    # Microsoft Planetary Computer (Geography Agent - FRD 10)
    MPC_STAC_URL: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    MPC_SIGNING_URL: str = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"
    MPC_COLLECTION: str = "sentinel-2-l2a"

    # Geocoding (Geography Agent)
    GEOCODING_SERVICE_URL: str = "https://nominatim.openstreetmap.org/search"
    GEOCODING_RATE_LIMIT_SECONDS: float = 1.0

    # Image Processing (Geography Agent)
    TEMP_IMAGE_DIR: str = "/tmp/sibyl-geography"
    MAX_TEMP_DIR_SIZE_GB: float = 5.0

    # Analysis thresholds (Geography Agent)
    NDVI_CHANGE_THRESHOLD: float = 0.1
    CLOUD_COVER_MAX_PREFERRED: float = 20.0
    CLOUD_COVER_MAX_ACCEPTABLE: float = 50.0


# Singleton settings instance
settings = Settings()
