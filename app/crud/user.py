from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.user import User
from typing import List, Optional, Dict, Any


class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    # 사용자 조회
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            text("SELECT * FROM users WHERE id = :user_id"), {"user_id": user_id}
        )
        return result.fetchone()

    # (내부 사용) 이메일로 사용자 조회
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            text("SELECT * FROM users WHERE email = :email"), {"email": email}
        )
        return result.fetchone()

    # (내부 사용) auth_provider와 auth_provider_id로 사용자 조회
    async def get_by_auth_provider_id(
        self, auth_provider: str, auth_provider_id: str
    ) -> Optional[User]:
        result = await self.db.execute(
            text(
                "SELECT * FROM users WHERE auth_provider = :auth_provider AND auth_provider_id = :auth_provider_id"
            ),
            {"auth_provider": auth_provider, "auth_provider_id": auth_provider_id},
        )
        return result.fetchone()

    # 사용자 생성
    async def create(self, user_data: Dict[str, Any]) -> User:
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    # (내부 사용) 사용자 목록 조회
    async def get_all(self) -> List[User]:
        result = await self.db.execute(text("SELECT * FROM users"))
        return result.fetchall()

    # 사용자 프로필 업데이트
    async def update_profile(
        self, user_id: int, update_data: Dict[str, Any]
    ) -> Optional[User]:
        if not update_data:
            return await self.get_by_id(user_id)

        # 동적으로 업데이트할 필드들만 포함
        set_clauses = []
        params = {"user_id": user_id}

        for field, value in update_data.items():
            if value is not None:
                set_clauses.append(f"{field} = :{field}")
                params[field] = value

        if not set_clauses:
            return await self.get_by_id(user_id)

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE users
            SET {', '.join(set_clauses)}
            WHERE id = :user_id
        """

        await self.db.execute(text(query), params)
        await self.db.commit()
        return await self.get_by_id(user_id)

    # 사용자 선호 아티스트 조회 (아티스트 ID 목록 반환)
    async def get_preferred_artist_ids(self, user_id: int) -> List[int]:
        result = await self.db.execute(
            text("SELECT artist_id FROM user_artists WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        rows = result.fetchall()
        return [row[0] for row in rows]  # artist_id만 추출

    # 사용자 선호 아티스트 추가
    async def add_preferred_artist(self, user_id: int, artist_id: int) -> None:
        await self.db.execute(
            text(
                "INSERT INTO user_artists (user_id, artist_id) VALUES (:user_id, :artist_id)"
            ),
            {"user_id": user_id, "artist_id": artist_id},
        )
        await self.db.commit()

    # 사용자 선호 아티스트 제거
    async def remove_preferred_artist(self, user_id: int, artist_id: int) -> None:
        await self.db.execute(
            text(
                "DELETE FROM user_artists WHERE user_id = :user_id AND artist_id = :artist_id"
            ),
            {"user_id": user_id, "artist_id": artist_id},
        )
        await self.db.commit()
