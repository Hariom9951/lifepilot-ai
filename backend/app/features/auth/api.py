import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses.schemas import SuccessResponse
from app.core.database.session import get_db_session
from app.core.exceptions.custom import UnauthorizedError
from app.features.auth.repositories import UserRepository
from app.features.auth.schemas import MessageResponse, TokenResponse, UserLogin, UserRegister, UserResponse
from app.features.auth.security import decode_token
from app.features.auth.services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    register_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Registers a new standard user with password validation and default role provisioning.
    """
    user = await AuthService.register_user(db, register_data)
    return SuccessResponse(
        message="User account successfully created.",
        data=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and retrieve tokens",
)
async def login(
    login_data: UserLogin,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Authenticates a user via email/username and password.
    Pushes a rotated Refresh Token to a secure HTTPOnly Cookie and returns the Access Token.
    """
    user, access_token, refresh_token = await AuthService.login_user(db, login_data)

    # Set HTTPOnly Secure cookie for refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",  # Scoped specifically to auth endpoint path for safety
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return SuccessResponse(
        message="Authentication successful.",
        data=TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        ),
    )


@router.post(
    "/logout",
    response_model=SuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Revoke active refresh token and sign out",
)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Signs out the current user session by revoking the active Refresh Token from the database.
    """
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await AuthService.logout_user(db, refresh_token)

    # Clear cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )

    return SuccessResponse(
        message="Sign out completed successfully.",
        data=MessageResponse(success=True, message="Session terminated."),
    )


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and acquire new access token",
)
async def refresh(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Performs token rotation. Evaluates the HTTPOnly refresh token cookie, rotates it,
    sets a new HTTPOnly cookie, and returns a new Access Token.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedError("Authentication refresh token is missing.")

    new_access_token, new_refresh_token = await AuthService.refresh_tokens(db, refresh_token)

    # Get user profile from the sub payload
    payload = decode_token(new_access_token, expected_type="access")
    user_uuid = uuid.UUID(payload["sub"])
    user = await UserRepository.get_by_id(db, user_uuid)
    if not user:
        raise UnauthorizedError("Associated user account no longer exists.")

    # Set rotated cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=7 * 24 * 60 * 60,
    )

    return SuccessResponse(
        message="Token refreshed successfully.",
        data=TokenResponse(
            access_token=new_access_token,
            user=UserResponse.model_validate(user),
        ),
    )
