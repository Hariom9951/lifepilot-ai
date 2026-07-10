import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings, settings
from app.core.database.session import get_db_session


# Settings DI provider
def get_settings() -> Settings:
    return settings


# DbSession DI provider mapping
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# Logger DI provider
def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)


# Future Authentication Placeholder
async def get_current_user_placeholder() -> dict:
    """
    Mock authentication placeholder to be fully implemented in a later sprint.
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "username": "mock_admin",
        "role": "admin",
    }
