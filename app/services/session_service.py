from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import UserCRUD
from app.schemas.auth import (
    CredentialDto,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    add_token_to_blacklist,
    verify_password,
)
from app.schemas.common import BaseResponse


class SessionService:
    def __init__(self, db: AsyncSession):
        self.user_crud = UserCRUD(db)

    async def create_token(self, user_id: int) -> CredentialDto:
        """토큰 생성"""
        return CredentialDto(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    async def refresh_token(self, refresh_token: str) -> CredentialDto:
        """토큰 갱신"""
        user_id = verify_refresh_token(refresh_token)
        return CredentialDto(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    async def login(self, login_data):
        """이메일 로그인"""
        from app.schemas.auth import SignInResponse
        from app.schemas.user import UserDto

        # 이메일로 사용자 찾기
        user = await self.user_crud.get_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 잘못되었습니다.",
            )

        # 비밀번호 확인 (일반 로그인의 경우)
        if login_data.password and user.hashed_password:
            if not verify_password(login_data.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 잘못되었습니다.",
                )

        # FCM 토큰 업데이트 (제공된 경우)
        if hasattr(login_data, "fcm_token") and login_data.fcm_token:
            await self.user_crud.update_profile(
                user.id, {"fcm_token": login_data.fcm_token}
            )

        # 토큰 생성
        credential = await self.create_token(user.id)

        # SignInResponse 생성
        sign_in_response = SignInResponse(
            credential=credential,
            user=UserDto.model_validate(user, from_attributes=True),
        )

        return sign_in_response

    async def logout(self, access_token: str, user_id: int = None):
        """로그아웃 (토큰 무효화 및 FCM 토큰 삭제)"""
        # 액세스 토큰을 블랙리스트에 추가하여 무효화
        add_token_to_blacklist(access_token)

        # FCM 토큰 삭제
        if user_id:
            await self.user_crud.update_profile(user_id, {"fcm_token": None})
