"""OAuth Router"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer

from app.common.schemas import BaseResponse
from app.deps.providers import get_oauth_use_case
from app.features.auth.schemas import LoginInfoDto
from app.features.oauth.schemas import (
    KakaoLoginRequest,
    OAuthProvider,
)
from app.features.oauth.use_cases.oauth_use_case import OAuthUseCase
from ._base import OAuthRouterLabel

security = HTTPBearer()


class KaKaoOauthRouter:
    router = APIRouter(
        prefix=OAuthRouterLabel.PREFIX.value,
        tags=[OAuthRouterLabel.TAG.value]
    )

    @staticmethod
    @router.post(
        path="/kakao",
        response_model=BaseResponse[LoginInfoDto],
        description="카카오 액세스 토큰을 통한 카카오 로그인",
    )
    async def kakao_login(
            request: KakaoLoginRequest,
            use_case: OAuthUseCase = Depends(get_oauth_use_case),
    ) -> BaseResponse[LoginInfoDto]:
        """ Kakao 액세스 토큰 로그인 """
        result = await use_case.sign_in_with_kakao(request)
        return BaseResponse.ok(data=result)

    @staticmethod
    @router.get(
        path="/kakao/login",
        response_class=RedirectResponse,
        status_code=307,
        description="카카오 로그인 시작 - 카카오 인증 페이지로 리다이렉트",
    )
    async def kakao_login_web(
            use_case: OAuthUseCase = Depends(get_oauth_use_case),
    ) -> RedirectResponse:
        kakao_auth_url = await use_case.get_auth_url(OAuthProvider.KAKAO)
        return RedirectResponse(url=kakao_auth_url)

    @staticmethod
    @router.get(
        path="/kakao/callback",
        include_in_schema=False,  # Swagger에서는 노출되지 않음
        description="카카오 OAuth 콜백의 인가코드를 통한 카카오 로그인",
    )
    async def kakao_callback(
            code: str | None = Query(None, description="인가 코드"),
            state: str | None = Query(None, description="상태값"),
            error_description: str | None = Query(None, description="에러 설명"),
            error: str | None = Query(None, description="에러 코드"),
            use_case: OAuthUseCase = Depends(get_oauth_use_case),
    ) -> BaseResponse[LoginInfoDto]:
        result = await use_case.handle_oauth_callback(
            provider=OAuthProvider.KAKAO,
            code=code,
            state=state,
            error=error,
            error_description=error_description,
        )
        return BaseResponse.ok(data=result)
