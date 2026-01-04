"""Session Use Case - 비즈니스 로직 처리"""

from app.core.security import verify_password
from app.core.session import (
    TokenInvalidError,
    add_token_to_blacklist,
    create_access_token,
    create_refresh_token,
    revoke_refresh_token,
    verify_refresh_token,
)
from app.features.auth.schemas import CredentialDto, LoginInfoDto
from app.features.session.repositories import SessionRepository
from app.features.users.exceptions import UserNotFoundException
from app.features.users.schemas import UserDetailDto
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class SessionUseCase:
    """세션 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        session_repo: SessionRepository,
    ):
        self._session = session
        self._session_repo = session_repo

    # - MARK: 이메일 로그인
    async def login(self, login_data) -> LoginInfoDto:
        """이메일 로그인"""
        # 이메일로 사용자 찾기
        user = await self._session_repo.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 잘못되었습니다.",
            )

        # 비밀번호 확인 (일반 로그인의 경우)
        user_hashed_password = getattr(user, "hashed_password", None)
        if login_data.password and user_hashed_password:
            if not verify_password(login_data.password, user_hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 잘못되었습니다.",
                )

        # FCM 토큰 업데이트 (제공된 경우)
        user_id = getattr(user, "id", None)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 ID를 가져올 수 없습니다.",
            )

        if hasattr(login_data, "fcm_token") and login_data.fcm_token:
            await self._update_fcm_token(user_id, login_data.fcm_token)

        # 토큰 생성
        credential = await self._create_token(user_id)

        # SignInResponse 생성
        return LoginInfoDto(
            credential=credential,
            user=UserDetailDto.model_validate(user, from_attributes=True),
        )

    # - MARK: 토큰 갱신
    async def refresh_token(self, refresh_token: str) -> CredentialDto:
        """토큰 갱신"""
        # 1. Refresh token 검증 (Redis 확인 포함)
        user_id = await verify_refresh_token(refresh_token)

        # 2. 유저 존재 및 상태 확인
        user = await self._session_repo.get_user_by_id(user_id)
        if not user:
            raise TokenInvalidError("User not found")

        if user.is_del:
            raise TokenInvalidError("User account has been deleted")

        # 3. 기존 리프레시 토큰 무효화 (Redis에서 삭제)
        await revoke_refresh_token(refresh_token)

        # 4. 새 토큰 발급
        return await self._create_token(user_id)

    # - MARK: 로그아웃
    async def logout(
        self, access_token: str, refresh_token: str | None = None, user_id: int | None = None
    ) -> None:
        """로그아웃 (토큰 무효화 및 FCM 토큰 삭제)"""
        # 액세스 토큰을 블랙리스트에 추가하여 무효화 (TTL: 30분)
        await add_token_to_blacklist(access_token, ttl_seconds=1800)

        # 리프레시 토큰 무효화 (Redis에서 삭제)
        if refresh_token:
            await revoke_refresh_token(refresh_token)

        # FCM 토큰 삭제
        if user_id:
            await self._update_fcm_token(user_id, None)

    # - MARK: 토큰 생성 (내부 메서드)
    async def _create_token(self, user_id: int) -> CredentialDto:
        """토큰 생성"""
        return CredentialDto(
            access_token=create_access_token(user_id),
            refresh_token=await create_refresh_token(user_id),
        )

    # - MARK: FCM 토큰 업데이트 (커밋 포함)
    async def _update_fcm_token(self, user_id: int, fcm_token: str | None) -> None:
        """사용자의 FCM 토큰 업데이트 (커밋 포함)"""
        await self._session_repo.update_fcm_token(user_id, fcm_token)
        await self._session.commit()
