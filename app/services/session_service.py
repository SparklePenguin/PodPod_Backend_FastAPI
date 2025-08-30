from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import UserCRUD
from app.schemas.auth import (
    Credential,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)


class SessionService:
    def __init__(self, db: AsyncSession):
        self.user_crud = UserCRUD(db)

    async def create_token(self, user_id: int) -> Credential:
        """토큰 생성"""
        return Credential(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    async def refresh_token(self, refresh_token: str) -> Credential:
        """토큰 갱신"""
        user_id = verify_token(refresh_token)
        return Credential(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
