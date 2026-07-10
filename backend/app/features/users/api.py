from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses.schemas import SuccessResponse
from app.core.database.session import get_db_session
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.auth.schemas import ProfileUpdate, UserResponse
from app.features.users.services import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve current user profile details",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Returns profile information for the currently logged-in user.
    """
    return SuccessResponse(
        message="User profile retrieved successfully.",
        data=UserResponse.model_validate(current_user),
    )


@router.patch(
    "/profile",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update current user profile information",
)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Updates designated profile fields (full name, avatar, timezone, language) for the authenticated user.
    """
    updated_user = await UserService.update_profile(db, current_user, profile_data)
    return SuccessResponse(
        message="User profile updated successfully.",
        data=UserResponse.model_validate(updated_user),
    )
