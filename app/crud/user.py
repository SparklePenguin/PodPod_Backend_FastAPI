from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.schemas.user import UserUpdate
from typing import List, Optional, Dict, Any


class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_data: Dict[str, Any]) -> User:
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            text("SELECT * FROM users WHERE email = :email"), {"email": email}
        )
        return result.fetchone()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            text("SELECT * FROM users WHERE id = :user_id"), {"user_id": user_id}
        )
        return result.fetchone()

    async def get_by_provider_id(self, provider_id: str) -> Optional[User]:
        result = await self.db.execute(
            text("SELECT * FROM users WHERE auth_provider_id = :provider_id"),
            {"provider_id": provider_id},
        )
        return result.fetchone()

    async def get_all(self) -> List[User]:
        result = await self.db.execute(text("SELECT * FROM users"))
        return result.fetchall()

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        update_data = user_data.dict(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(user_id)

        await self.db.execute(
            text(
                """
                UPDATE users 
                SET username = COALESCE(:username, username),
                    full_name = COALESCE(:full_name, full_name),
                    profile_image = COALESCE(:profile_image, profile_image),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
                """
            ),
            {**update_data, "user_id": user_id},
        )
        await self.db.commit()
        return await self.get_by_id(user_id)
