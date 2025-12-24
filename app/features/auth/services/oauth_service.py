from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.schemas import CredentialDto, SignInResponse, SignUpRequest
from app.features.auth.services.session_service import SessionService
from app.features.users.repositories import UserRepository
from app.features.users.services import UserService


# - MARK: OAuth 서비스
class OauthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_crud = UserRepository(db)
        self.user_service = UserService(db)
        self.session_service = SessionService(db)

    # - MARK: OAuth 로그인 처리 (범용)
    async def sign_in_with_oauth(
        self,
        oauth_provider: str,
        oauth_user_id: str,
        oauth_user_info: Dict[str, Any],
        fcm_token: str | None = None,
    ):
        """OAuth 로그인 처리 (범용)"""
        try:
            # 기존 사용자 확인 (auth_provider_id로, 삭제된 사용자 포함)
            existing_user_raw = await self.user_crud.get_by_auth_provider_id(
                auth_provider=oauth_provider, auth_provider_id=str(oauth_user_id)
            )

            if existing_user_raw:
                # 소프트 삭제된 사용자인 경우 복구
                is_del_value = getattr(existing_user_raw, 'is_del', False)
                if is_del_value:
                    from sqlalchemy import update

                    from app.features.users.models import User

                    await self.db.execute(
                        update(User)
                        .where(User.id == existing_user_raw.id)
                        .values(
                            is_del=False,
                            is_active=True,
                            nickname=oauth_user_info.get("nickname")
                            or existing_user_raw.nickname,
                            profile_image=oauth_user_info.get("image_url")
                            or existing_user_raw.profile_image,
                            email=oauth_user_info.get("email")
                            or existing_user_raw.email,
                            fcm_token=fcm_token or existing_user_raw.fcm_token,
                        )
                    )
                    await self.db.commit()
                    await self.db.refresh(existing_user_raw)

                # 기존 사용자 정보 조회 (복구된 경우 포함)
                existing_user = await self.user_service.get_user_by_auth_provider_id(
                    auth_provider=oauth_provider, auth_provider_id=str(oauth_user_id)
                )

                if existing_user:
                    # 기존 사용자가 있으면 FCM 토큰 업데이트
                    user = existing_user
                    if fcm_token:
                        await self.user_crud.update_profile(
                            existing_user.id, {"fcm_token": fcm_token}
                        )
            else:
                # 새 사용자 생성
                user = await self.user_service.create_user(
                    SignUpRequest(
                        email=oauth_user_info.get("email"),
                        username=oauth_user_info.get("username"),
                        nickname=oauth_user_info.get("nickname"),
                        profile_image=oauth_user_info.get("image_url"),
                        auth_provider=oauth_provider,
                        auth_provider_id=str(oauth_user_id),
                        fcm_token=fcm_token,
                    )
                )

            # 토큰 발급
            token_response = await self.session_service.create_token(user.id)

            sign_in_response = SignInResponse(
                credential=CredentialDto(
                    access_token=token_response.access_token,
                    refresh_token=token_response.refresh_token,
                ),
                user=user,  # user는 이미 UserDto 타입
            )

            return sign_in_response

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )
