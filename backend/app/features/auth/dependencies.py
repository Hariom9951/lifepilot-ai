import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db_session
from app.core.exceptions.custom import ForbiddenError, UnauthorizedError
from app.features.auth.models import User
from app.features.auth.repositories import UserRepository
from app.features.auth.security import decode_token

# Bearer security scheme
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    Dependency to validate JWT Access Token and return the current authenticated User.
    """
    if not credentials:
        raise UnauthorizedError("Authentication credentials were not provided.")

    token = credentials.credentials
    payload = decode_token(token, expected_type="access")

    try:
        user_uuid = uuid.UUID(payload.get("sub"))
    except (ValueError, TypeError) as e:
        raise UnauthorizedError("Token contains an invalid user identifier.") from e

    user = await UserRepository.get_by_id(db, user_uuid)
    if not user:
        raise UnauthorizedError("User session no longer exists.")

    if not user.is_active:
        raise ForbiddenError("User account has been deactivated.")

    return user


class RequireRole:
    """
    FastAPI dependency creator to restrict endpoints based on Role-Based Access Control (RBAC).
    """

    def __init__(self, *allowed_roles: str) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role.name not in self.allowed_roles:
            raise ForbiddenError(
                f"Access denied. Required role: {', '.join(self.allowed_roles)}. "
                f"Your role: {current_user.role.name}."
            )
        return current_user
