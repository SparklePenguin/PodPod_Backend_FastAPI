from email import message
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel, Field
from app.services.oauth_service import OauthService
from app.schemas.common import SuccessResponse, ErrorResponse
from app.core.config import settings


# - MARK: 구글 로그인 요청
class GoogleLoginRequest(BaseModel):
    id_token: str = Field(alias="idToken")

    model_config = {
        "populate_by_name": True,
    }


class GoogleOauthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oauth_service = OauthService(db)

    def verify_google_token(self, token: str) -> dict:
        """Google ID 토큰 검증"""
        try:
            # Google 클라이언트 ID 설정 필요
            client_id = settings.GOOGLE_CLIENT_ID
            if not client_id:
                raise ValueError("Google Client ID not configured")

            id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
            return id_info
        except Exception as e:
            raise ValueError(f"Invalid Google token: {str(e)}") from e

    async def sign_in_with_google(
        self, google_login_request: GoogleLoginRequest
    ) -> SuccessResponse:
        """Google 로그인 처리"""
        try:
            # Google 토큰 검증
            google_user_info = self.verify_google_token(
                google_login_request.id_token,
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="invalid_google_token",
                    status=status.HTTP_400_BAD_REQUEST,
                    message=str(e),
                ).model_dump(),
            )

        # Google 사용자 정보를 OAuth 서비스 형식에 맞게 변환
        google_user_info["username"] = google_user_info.get("name")
        google_user_info["image_url"] = google_user_info.get("picture")

        return await self.oauth_service.sign_in_with_oauth(
            oauth_provider="google",
            oauth_user_id=str(google_user_info["sub"]),
            oauth_user_info=google_user_info,
        )
