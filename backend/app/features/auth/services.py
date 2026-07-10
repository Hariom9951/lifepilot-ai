import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.custom import ValidationError
from app.features.auth.exceptions import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.features.auth.models import User
from app.features.auth.repositories import (
    RefreshTokenRepository,
    RoleRepository,
    UserRepository,
)
from app.features.auth.schemas import UserLogin, UserRegister
from app.features.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)


def _hash_jwt_token(token: str) -> str:
    """
    Hash a JWT refresh token using SHA-256 for secure database storage and fast index lookups.
    """
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    """
    Service Layer implementing business logic for authentication.
    """

    @staticmethod
    async def register_user(db: AsyncSession, register_data: UserRegister) -> User:
        # Validate password strength requirements
        try:
            validate_password_strength(register_data.password)
        except ValueError as e:
            raise ValidationError(message=str(e)) from e

        # Check unique constraint: Email
        existing_email = await UserRepository.get_by_email(db, register_data.email)
        if existing_email:
            raise DuplicateEmailError()

        # Check unique constraint: Username
        existing_username = await UserRepository.get_by_username(
            db, register_data.username
        )
        if existing_username:
            raise DuplicateUsernameError()

        # Resolve the default role
        role = await RoleRepository.get_by_name(db, "USER")
        if not role:
            # Seed the default USER role if it does not exist
            role = await RoleRepository.create(
                db, name="USER", description="Standard client account permission tier."
            )

        hashed = hash_password(register_data.password)
        user_dict = {
            "full_name": register_data.full_name,
            "username": register_data.username,
            "email": register_data.email,
            "hashed_password": hashed,
            "role_id": role.id,
            "timezone": register_data.timezone,
            "language": register_data.language,
            "is_active": True,
            "is_verified": False,
        }

        user = await UserRepository.create(db, user_dict)
        await db.commit()
        return user

    @staticmethod
    async def login_user(
        db: AsyncSession, login_data: UserLogin
    ) -> tuple[User, str, str]:
        # Support login via email OR username
        if "@" in login_data.username_or_email:
            user = await UserRepository.get_by_email(db, login_data.username_or_email)
        else:
            user = await UserRepository.get_by_username(
                db, login_data.username_or_email
            )

        if not user or not user.is_active:
            raise InvalidCredentialsError()

        # Verify Argon2 hash matches password
        if not verify_password(user.hashed_password, login_data.password):
            raise InvalidCredentialsError()

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        # Hash and store refresh token
        hashed_rt = _hash_jwt_token(refresh_token)
        expires_at = datetime.now(UTC) + timedelta(days=7)
        await RefreshTokenRepository.create(db, user.id, hashed_rt, expires_at)

        # Update last login timestamp
        await UserRepository.update(db, user, {"last_login": datetime.now(UTC)})
        await db.commit()

        return user, access_token, refresh_token

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession, raw_refresh_token: str
    ) -> tuple[str, str]:
        # Validate and decode JWT Refresh Token
        payload = decode_token(raw_refresh_token, expected_type="refresh")
        user_uuid = uuid.UUID(payload["sub"])

        hashed_rt = _hash_jwt_token(raw_refresh_token)
        db_token = await RefreshTokenRepository.get_by_token(db, hashed_rt)

        if not db_token:
            raise InvalidTokenError("Refresh token not found.")

        # Re-use detection: if token is already marked revoked, suspect theft!
        if db_token.revoked:
            # Revoke all tokens for this user for security
            await RefreshTokenRepository.revoke_all_for_user(db, user_uuid)
            await db.commit()
            raise InvalidTokenError("Refresh token has been reused. Revoking session.")

        # Expiry check
        if db_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            await RefreshTokenRepository.revoke(db, db_token.id)
            await db.commit()
            raise TokenExpiredError("Refresh token has expired.")

        # Rotate tokens: revoke the old one, generate a new pair
        await RefreshTokenRepository.revoke(db, db_token.id)

        new_access_token = create_access_token(user_uuid)
        new_refresh_token = create_refresh_token(user_uuid)

        new_hashed_rt = _hash_jwt_token(new_refresh_token)
        new_expires_at = datetime.now(UTC) + timedelta(days=7)
        await RefreshTokenRepository.create(
            db, user_uuid, new_hashed_rt, new_expires_at
        )

        await db.commit()
        return new_access_token, new_refresh_token

    @staticmethod
    async def logout_user(db: AsyncSession, raw_refresh_token: str) -> None:
        # Decode first to check validity
        try:
            decode_token(raw_refresh_token, expected_type="refresh")
        except Exception:
            # Even if invalid, attempt to clear db if match is found
            pass

        hashed_rt = _hash_jwt_token(raw_refresh_token)
        db_token = await RefreshTokenRepository.get_by_token(db, hashed_rt)
        if db_token:
            await RefreshTokenRepository.revoke(db, db_token.id)
            await db.commit()
