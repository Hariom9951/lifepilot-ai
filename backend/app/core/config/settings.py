import os
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "LifePilot AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "local"
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

    # Production Embedding Engine Configs
    EMBEDDING_PROVIDER: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_CACHE_ENABLED: bool = True

    # Vector Storage Configurations
    VECTOR_PROVIDER: str = "chroma"
    CHROMA_DB_PATH: str = "./storage/chroma"
    QDRANT_URL: str = "http://localhost:6333"

    def get_masked_settings(self) -> dict[str, Any]:
        """
        Mask sensitive credentials (keys, passwords, URLs) to prevent leaking in logs.
        """
        masked = {}
        for k, v in self.model_dump().items():
            k_lower = k.lower()
            if any(x in k_lower for x in ["secret", "password", "url", "key"]):
                masked[k] = "********"
            else:
                masked[k] = v
        return masked


class LocalSettings(Settings):
    ENVIRONMENT: str = "local"
    DEBUG: bool = True


class StagingSettings(Settings):
    ENVIRONMENT: str = "staging"
    DEBUG: bool = False


class ProductionSettings(Settings):
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_production_secret(cls, v: str) -> str:
        if (
            v == "replace_me_with_a_secure_random_hex_string_sprinting_phase"
            or len(v) < 16
        ):
            raise ValueError(
                "SECRET_KEY must be a secure random string of at least 16 characters in production."
            )
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_production_db(cls, v: str) -> str:
        if (
            "localhost" in v
            or "127.0.0.1" in v
            or "lifepilot_secure_password_replace_me" in v
        ):
            raise ValueError(
                "DATABASE_URL must point to a secure, remote production database."
            )
        return v

    @field_validator("REDIS_URL")
    @classmethod
    def validate_production_redis(cls, v: str) -> str:
        if (
            "localhost" in v
            or "127.0.0.1" in v
            or "redis_secure_password_replace_me" in v
        ):
            raise ValueError(
                "REDIS_URL must point to a secure, remote production Redis server."
            )
        return v


def get_settings() -> Settings:
    env = os.getenv("ENVIRONMENT", "local").lower()
    if env == "production":
        return ProductionSettings()
    elif env == "staging":
        return StagingSettings()
    else:
        return LocalSettings()


settings = get_settings()
