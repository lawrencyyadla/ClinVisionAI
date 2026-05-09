from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "ClinVision AI"
    API_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "local"

    DATABASE_URL: str = "postgresql+psycopg2://clinvision:clinvision@localhost:5432/clinvision"
    REDIS_URL: str = "redis://localhost:6379/0"

    CORS_ORIGINS: str = "http://localhost:3000"
    MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024

    DATA_DIR: Path = Path("data")
    UPLOAD_DIR: Path = Path("data/uploads")
    CONVERTED_DIR: Path = Path("data/converted")
    HEATMAP_DIR: Path = Path("data/heatmaps")

    CELERY_TASK_TIME_LIMIT_SECONDS: int = 180
    CELERY_TASK_SOFT_TIME_LIMIT_SECONDS: int = 150
    CELERY_RESULT_EXPIRES_SECONDS: int = 3600
    REDIS_TASK_TTL_SECONDS: int = 3600

    MODEL_NAME: str = "DenseNet121"
    MODEL_VERSION: str = "densenet121-v1.0.0-demo"
    MODEL_CHECKPOINT_PATH: str = ""
    MODEL_HASH: str = "demo-unvalidated"

    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_TIMEOUT_SECONDS: int = 8

    FRONTEND_POLL_TIMEOUT_MS: int = 180000

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
