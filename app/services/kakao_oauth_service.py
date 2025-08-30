from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.common import SuccessResponse, ErrorResponse
from app.services.oauth_service import OauthService
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from pydantic import BaseModel, Field


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


# - MARK: 카카오 로그인 요청
class KakaoLoginRequest(BaseModel):
    access_token: str = Field(alias="accessToken")  # 사용자 액세스 토큰 값
    id_token: Optional[str] = Field(
        default=None, alias="idToken"
    )  # ID 토큰 값 (OpenID Connect)
    expires_in: str = Field(alias="expiresIn")  # 액세스 토큰과 ID 토큰의 만료 시간(초)
    refresh_token: Optional[str] = Field(
        default=None, alias="refreshToken"
    )  # 사용자 리프레시 토큰 값
    refresh_token_expires_in: Optional[str] = Field(
        alias="refreshTokenExpiresIn"
    )  # 리프레시 토큰 만료 시간(초)
    scopes: List[str] = Field(
        default=[], alias="scopes"
    )  # 인증된 사용자의 정보 조회 권한 범위

    model_config = {
        "populate_by_name": True,
    }


# - MARK: 카카오 토큰 응답 리스폰
class KakaoTokenResponse(BaseModel):
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

    model_config = {
        "populate_by_name": True,
    }


# - MARK: 사용자 정보 응답
class _Profile(BaseModel):
    nickname: Optional[str] = None
    thumbnail_image_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_default_image: Optional[bool] = None
    is_default_nickname: Optional[bool] = None


# - MARK: 카카오 사용자 정보 응답
# https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#kakaoaccount
# https://developers.kakao.com/console/app/1301346/product/login/scope
class _KakaoAccount(BaseModel):
    profile_image_needs_agreement: Optional[bool] = None
    profile: Optional[_Profile] = None


# - MARK: 카카오 사용자 정보 응답
class _KakaoUserInfoResponse(BaseModel):
    id: int  # 카카오 회원번호
    connected_at: str  # 서비스에 연결 완료된 시각
    properties: Optional[_Profile] = None  # 사용자 프로퍼티
    kakao_account: Optional[_KakaoAccount] = None  # 카카오계정 정보


# - MARK: 카카오 OAuth 서비스
class KakaoOauthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.oauth_service = OauthService(db)
        self.redirect_uri = settings.KAKAO_REDIRECT_URI
        self.kakao_token_url = settings.KAKAO_TOKEN_URL
        self.kakao_user_info_url = settings.KAKAO_USER_INFO_URL

    async def sign_in_with_kakao(
        self, kakao_sign_in_request: KakaoTokenResponse
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

        # 카카오 사용자 정보를 OAuth 서비스 형식에 맞게 변환
        oauth_user_info = kakao_user_info.model_dump(by_alias=True)
        oauth_user_info["image_url"] = (
            kakao_user_info.kakao_account.profile.profile_image_url
        )

        return await self.oauth_service.sign_in_with_oauth(
            oauth_provider="kakao",
            oauth_user_id=str(kakao_user_info.id),
            oauth_user_info=oauth_user_info,
        )

    async def handle_kakao_callback(
        self, params: KakaoCallBackParam
    ) -> SuccessResponse:
        """카카오 콜백 처리"""
        # 인가 코드 요청 실패 처리
        if params.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="kakao_oauth_error",
                    status=400,
                    message=params.error,
                ),
            )

        # 인가 코드가 없는 경우
        if not params.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="missing_authorization_code",
                    status=400,
                    message=params.error,
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

        return await self.sign_in_with_kakao(token_response)

    # - MARK: 토큰 요청
    async def get_kakao_token(
        self, code: str, redirect_uri: str = None
    ) -> KakaoTokenResponse:
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
                data=token_params.model_dump(exclude_none=True),
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
                        message=response.text,
                    ),
                )

            return KakaoTokenResponse(**response.json())

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
                        message=response.text,
                    ),
                )

            return _KakaoUserInfoResponse(**response.json())
