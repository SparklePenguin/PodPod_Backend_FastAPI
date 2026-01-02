from app.core.session import create_access_token, create_refresh_token
from app.features.auth.schemas import CredentialDto
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    # - MARK: 토큰 생성
    async def create_credential(self, user_id: int) -> CredentialDto:
        """토큰 생성 (리프레시 토큰은 Redis에 저장)"""
        return CredentialDto(
            access_token=create_access_token(user_id),
            refresh_token=await create_refresh_token(user_id),
        )
