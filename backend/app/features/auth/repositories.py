import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.auth.models import RefreshToken, Role, User


class RoleRepository:
    """
    Asynchronous Repository for Roles.
    """

    @staticmethod
    async def get_by_id(db: AsyncSession, role_id: uuid.UUID) -> Role | None:
        stmt = select(Role).where(Role.id == role_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession, name: str, description: str | None = None, permissions: Any | None = None
    ) -> Role:
        role = Role(
            name=name,
            description=description,
            permissions=permissions or []
        )
        db.add(role)
        await db.flush()
        return role


class UserRepository:
    """
    Asynchronous Repository for Users.
    """

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email).options(selectinload(User.role))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        stmt = select(User).where(User.username == username).options(selectinload(User.role))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_data: dict[str, Any]) -> User:
        user = User(**user_data)
        db.add(user)
        await db.flush()
        # Eagerly load the role relationship
        stmt = select(User).where(User.id == user.id).options(selectinload(User.role))
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def update(db: AsyncSession, user: User, update_data: dict[str, Any]) -> User:
        for key, value in update_data.items():
            if value is not None:
                setattr(user, key, value)
        db.add(user)
        await db.flush()
        return user


class RefreshTokenRepository:
    """
    Asynchronous Repository for Refresh Tokens.
    """

    @staticmethod
    async def get_by_token(db: AsyncSession, hashed_token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.hashed_token == hashed_token)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession, user_id: uuid.UUID, hashed_token: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            hashed_token=hashed_token,
            expires_at=expires_at
        )
        db.add(token)
        await db.flush()
        return token

    @staticmethod
    async def revoke(db: AsyncSession, token_id: uuid.UUID) -> None:
        stmt = update(RefreshToken).where(RefreshToken.id == token_id).values(revoked=True)
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def revoke_all_for_user(db: AsyncSession, user_id: uuid.UUID) -> None:
        stmt = update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        await db.execute(stmt)
        await db.flush()
