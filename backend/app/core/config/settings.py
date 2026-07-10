from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "LifePilot AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "replace_me_with_a_secure_random_hex_string_sprinting_phase"
    LOG_LEVEL: str = "info"

    # CORS
    CORS_ORIGINS: str | list[str] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list | str):
            return v
        return []

    # Database & Redis URLs
    DATABASE_URL: str = (
        "postgresql+asyncpg://lifepilot_user:lifepilot_secure_password_replace_me@localhost:5432/lifepilot_db"
    )
    REDIS_URL: str = "redis://:redis_secure_password_replace_me@localhost:6379/0"

    # Knowledge / RAG Configuration
    KNOWLEDGE_UPLOAD_DIR: str = "./storage/uploads"
    KNOWLEDGE_VECTOR_DIR: str = "./storage/faiss"
    KNOWLEDGE_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    KNOWLEDGE_CHUNK_SIZE: int = 512
    KNOWLEDGE_CHUNK_OVERLAP: int = 64
    KNOWLEDGE_MAX_FILE_SIZE_MB: int = 25


settings = Settings()
