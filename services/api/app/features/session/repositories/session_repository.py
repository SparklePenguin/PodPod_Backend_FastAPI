from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class SessionRepository:
    """세션 관련 데이터베이스 작업"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepository(session)

    # - MARK: 이메일로 사용자 조회
    async def get_user_by_email(self, email: str):
        """이메일로 사용자 조회"""
        return await self._user_repo.get_by_email(email)

    # - MARK: ID로 사용자 조회
    async def get_user_by_id(self, user_id: int):
        """ID로 사용자 조회"""
        return await self._user_repo.get_by_id(user_id)

    # - MARK: FCM 토큰 업데이트
    async def update_fcm_token(self, user_id: int, fcm_token: str | None) -> None:
        """사용자의 FCM 토큰 업데이트"""
        await self._user_repo.update_fcm_token(user_id, fcm_token)
