from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User
from app.features.auth.repositories import UserRepository
from app.features.auth.schemas import ProfileUpdate


class UserService:
    """
    Service Layer implementing business logic for profile management.
    """

    @staticmethod
    async def update_profile(db: AsyncSession, user: User, update_data: ProfileUpdate) -> User:
        # Convert update schema to dictionary mapping
        data_to_update = update_data.model_dump(exclude_unset=True)
        
        updated_user = await UserRepository.update(db, user, data_to_update)
        await db.commit()
        return updated_user
