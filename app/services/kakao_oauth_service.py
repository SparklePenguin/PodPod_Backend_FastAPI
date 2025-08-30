from typing import Dict, Any, Optional, List
from app.schemas.auth import (
    Credential,
    SignInResponse,
    SignUpRequest,
    UserDto,
)


from app.schemas.common import SuccessResponse, ErrorResponse
from app.services.session_service import SessionService
from app.core.database import get_db
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from pydantic import BaseModel, ConfigDict, Field
from app.services.user_service import UserService


# - MARK: 콜백 쿼리
class KakaoCallBackParam(BaseModel):
    code: Optional[str] = None  # 토큰 요청에 필요한 인가 코드
    error: Optional[str] = None  # 인증 실패 시 반환되는 에러 코드
    error_description: Optional[str] = None  # 인증 실패 시 반환되는 에러 메시지
    state: Optional[str] = None  # 요청 시 전달한 state 값과 동일한 값


# - MARK: 토큰 요청 파라미터
class _GetTokenParam(BaseModel):
    grant_type: str = "authorization_code"  # authorization_code로 고정
    client_id: str  # 앱 REST API 키
    redirect_uri: str  # 인가 코드가 리다이렉트된 URI
    code: str  # 인가 코드 요청으로 얻은 인가 코드
    client_secret: Optional[str] = None  # 토큰 발급 시 보안 강화용 코드


# - MARK: 카카오 로그인 Request & 토큰 응답 리스폰
class KakaoSignInRequest(BaseModel):
    token_type: str = Field(
        default="bearer", alias="tokenType"
    )  # 토큰 타입, bearer로 고정
    access_token: str = Field(alias="accessToken")  # 사용자 액세스 토큰 값
    id_token: Optional[str] = Field(
        default=None, alias="idToken"
    )  # ID 토큰 값 (OpenID Connect)
    expires_in: str = Field(alias="expiresIn")  # 액세스 토큰과 ID 토큰의 만료 시간(초)
    refresh_token: str = Field(alias="refreshToken")  # 사용자 리프레시 토큰 값
    refresh_token_expires_in: str = Field(
        alias="refreshTokenExpiresIn"
    )  # 리프레시 토큰 만료 시간(초)
    scope: List[str] = Field(
        default=[], alias="scope"
    )  # 인증된 사용자의 정보 조회 권한 범위

    model_config = ConfigDict(
        populate_by_name=True,
    )


# - MARK: 사용자 정보 응답
class _Profile(BaseModel):
    nickname: Optional[str] = None
    thumbnail_image_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_default_image: Optional[bool] = None
    is_default_nickname: Optional[bool] = None


# - MARK: 카카오 사용자 정보 응답
class _KakaoAccount(BaseModel):
    profile_needs_agreement: Optional[bool] = None
    profile: Optional[_Profile] = None
    has_email: Optional[bool] = None
    email_needs_agreement: Optional[bool] = None
    is_email_valid: Optional[bool] = None
    is_email_verified: Optional[bool] = None
    email: Optional[str] = None
    has_age_range: Optional[bool] = None
    age_range_needs_agreement: Optional[bool] = None
    has_birthday: Optional[bool] = None
    birthday_needs_agreement: Optional[bool] = None
    has_gender: Optional[bool] = None
    gender_needs_agreement: Optional[bool] = None


# - MARK: 카카오 사용자 정보 응답
class _KakaoUserInfoResponse(BaseModel):
    id: int  # 카카오 회원번호
    connected_at: str  # 서비스에 연결 완료된 시각
    properties: Optional[_Profile] = None  # 사용자 프로퍼티
    kakao_account: Optional[_KakaoAccount] = None  # 카카오계정 정보


# - MARK: 카카오 OAuth 서비스
class KakaoOauthService:
    def __init__(
        self, user_service: UserService, session_service: SessionService
    ) -> None:
        self.redirect_uri = settings.KAKAO_REDIRECT_URI
        self.kakao_token_url = settings.KAKAO_TOKEN_URL
        self.kakao_user_info_url = settings.KAKAO_USER_INFO_URL

    async def sign_in_with_kakao(
        self, kakao_sign_in_request: KakaoSignInRequest
    ) -> SuccessResponse:
        try:
            kakao_user_info = await self.get_kakao_user_info(
                kakao_sign_in_request.access_token
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error="user_info_request_failed",
                    status=500,
                    message=str(e),
                ),
            )

        # 사용자 정보 저장
        async for db in get_db():
            user_service = UserService(db)

            # 기존 사용자 확인 (auth_provider_id로)
            existing_user = await user_service.get_user_by_auth_provider_id(
                auth_provider="kakao", auth_provider_id=str(kakao_user_info.id)
            )

            if existing_user:
                # 기존 사용자가 있으면 그 사용자로 로그인
                user = existing_user
            else:
                # 새 사용자 생성
                user = await user_service.create_user(
                    SignUpRequest(
                        email=kakao_user_info.kakao_account.email,
                        username=kakao_user_info.kakao_account.profile.nickname,
                        full_name=kakao_user_info.kakao_account.profile.nickname,
                        profile_image=kakao_user_info.kakao_account.profile.profile_image_url,
                        auth_provider="kakao",
                        auth_provider_id=str(kakao_user_info.id),
                    )
                )

            # 토큰 발급
            session_service = SessionService(db)
            token_response = await session_service.create_token(
                user.id,
            )
            break

        return SuccessResponse(
            code=200,
            message="kakao_login_success",
            data=SignInResponse(
                credential=Credential(
                    access_token=token_response.access_token,
                    refresh_token=token_response.refresh_token,
                ),
                user=UserDto(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    profile_image=user.profile_image,
                    full_name=user.full_name,
                    needs_onboarding=user.needs_onboarding,
                ),
            ),
        )

    async def handle_kakao_callback(self, params: KakaoCallBackParam) -> SignInResponse:
        """카카오 콜백 처리"""
        # 인가 코드 요청 실패 처리
        if params.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code=params.error,
                    status=400,
                    message=params.error_description,
                ),
            )

        # 인가 코드가 없는 경우
        if not params.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code=params.error,
                    status=400,
                    message=params.error_description,
                ),
            )

        # 토큰 요청
        try:
            # 1. 인가 코드로 토큰 요청
            token_response = await self.get_kakao_token(
                code=params.code, redirect_uri=self.redirect_uri
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error="token_request_failed", status=500, message=str(e)
                ),
            )

        return self.sign_in_with_kakao(token_response)

    # - MARK: 토큰 요청
    async def get_kakao_token(
        self, code: str, redirect_uri: str = None
    ) -> _KakaoUserInfoResponse:
        """카카오 OAuth 인증 코드로 액세스 토큰을 가져옴"""

        # 설정에서 카카오 정보 가져오기
        client_id = settings.KAKAO_CLIENT_ID
        client_secret = settings.KAKAO_CLIENT_SECRET
        redirect_uri = redirect_uri or settings.KAKAO_REDIRECT_URI

        token_params = _GetTokenParam(
            client_id=client_id,
            redirect_uri=redirect_uri,
            code=code,
            client_secret=client_secret,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.kakao_token_url,
                data=token_params.dict(exclude_none=True),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error_code="get_kakao_token_failed",
                        status=response.status_code,
                        message="get_kakao_token_failed",
                    ),
                )

            return KakaoSignInRequest(**response.json())

    # - MARK: 사용자 정보 요청
    async def get_kakao_user_info(self, access_token: str) -> _KakaoUserInfoResponse:
        """카카오 액세스 토큰으로 사용자 정보를 가져옴"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.kakao_user_info_url,
                headers={
                    "Authorization": "Bearer " + access_token,
                    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error_code="get_kakao_user_info_failed",
                        status=response.status_code,
                        message="get_kakao_user_info_failed",
                    ),
                )

            return _KakaoUserInfoResponse(**response.json())
