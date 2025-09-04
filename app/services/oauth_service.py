from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.crud.user import UserCRUD
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.schemas.auth import CredentialDto, SignUpRequest, SignInResponse
from app.schemas.user import UserDto
from app.schemas.common import SuccessResponse, ErrorResponse


# - MARK: OAuth 서비스
class OauthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_crud = UserCRUD(db)
        self.user_service = UserService(db)
        self.session_service = SessionService(db)

    # - MARK: OAuth 로그인 처리 (범용)
    async def sign_in_with_oauth(
        self, oauth_provider: str, oauth_user_id: str, oauth_user_info: Dict[str, Any]
    ) -> SuccessResponse:
        """OAuth 로그인 처리 (범용)"""
        try:
            # 기존 사용자 확인 (auth_provider_id로)
            existing_user = await self.user_service.get_user_by_auth_provider_id(
                auth_provider=oauth_provider, auth_provider_id=str(oauth_user_id)
            )

            if existing_user:
                # 기존 사용자가 있으면 그 사용자로 로그인
                user = existing_user
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

            return SuccessResponse(
                code=200,
                message=f"{oauth_provider}_login_success",
                data=sign_in_response.model_dump(by_alias=True),
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error_code=f"{oauth_provider}_login_failed",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=str(e),
                ).model_dump(),
            )
