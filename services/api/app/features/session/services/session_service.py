from app.core.security import (
    add_token_to_blacklist,
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_refresh_token,
)
from app.features.auth.schemas.credential_dto import CredentialDto
from app.features.auth.schemas.login_info_dto import LoginInfoDto
from app.features.session.repositories import SessionRepository
from app.features.users.schemas import UserDetailDto
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class SessionService:
    def __init__(self, session: AsyncSession):
        self._session_repo = SessionRepository(session)

    # - MARK: 토큰 생성
    async def create_token(self, user_id: int) -> CredentialDto:
        """토큰 생성"""
        return CredentialDto(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    # - MARK: 토큰 갱신
    async def refresh_token(self, refresh_token: str) -> CredentialDto:
        """토큰 갱신"""
        user_id = verify_refresh_token(refresh_token)
        return CredentialDto(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    # - MARK: 이메일 로그인
    async def login(self, login_data):
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
            await self._session_repo.update_fcm_token(user_id, login_data.fcm_token)

        # 토큰 생성
        credential = await self.create_token(user_id)

        # SignInResponse 생성
        sign_in_response = LoginInfoDto(
            credential=credential,
            user=UserDetailDto.model_validate(user, from_attributes=True),
        )

        return sign_in_response

    # - MARK: 로그아웃
    async def logout(self, access_token: str, user_id: int | None = None):
        """로그아웃 (토큰 무효화 및 FCM 토큰 삭제)"""
        # 액세스 토큰을 블랙리스트에 추가하여 무효화
        add_token_to_blacklist(access_token)

        # FCM 토큰 삭제
        if user_id:
            await self._session_repo.update_fcm_token(user_id, None)

    # - MARK: Refresh Token 검증
    @staticmethod
    def verify_refresh_token(refresh_token: str) -> int:
        """Refresh Token 검증 및 user_id 반환 (정적 메서드)"""
        return verify_refresh_token(refresh_token)

    # - MARK: Access Token 생성
    @staticmethod
    def create_access_token(user_id: int) -> str:
        """Access Token 생성 (정적 메서드)"""
        return create_access_token(user_id)
