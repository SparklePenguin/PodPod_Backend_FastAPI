from app.core.session import TokenManager
from app.features.auth.schemas import CredentialDto
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

        self._token_manager = TokenManager()

    # - MARK: 토큰 생성
    async def create_credential(self, user_id: int) -> CredentialDto:
        """토큰 생성 (리프레시 토큰은 Redis에 저장)"""
        return CredentialDto(
            accessToken=self._token_manager.create_access_token(user_id),
            refreshToken=await self._token_manager.create_refresh_token(user_id)
        )
