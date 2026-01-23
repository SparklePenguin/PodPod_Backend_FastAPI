from fastapi import APIRouter, Depends, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer

from app.common.schemas import BaseResponse
from app.deps.providers import get_oauth_use_case
from app.features.auth.schemas import LoginInfoDto
from app.features.oauth.schemas import (
    AppleLoginRequest,
    OAuthProvider,
)
from app.features.oauth.use_cases.oauth_use_case import OAuthUseCase
from ._base import OAuthRouterRootLabel, AppleOauthRouterLabel

security = HTTPBearer()


class AppleOauthRouter:
    router = APIRouter(
        prefix=OAuthRouterRootLabel.PREFIX,
        tags=[AppleOauthRouterLabel.TAG]
    )

    @staticmethod
    @router.get(
        f"/{AppleOauthRouterLabel.PREFIX}/login",
        response_class=RedirectResponse,
        status_code=307,
        description="Apple 로그인 시작 - Apple 인증 페이지로 리다이렉트",
    )
    async def apple_login_web(
            base_url: str | None = Query(None, description="테스트용 Base URL (예: ngrok URL)"),
            use_case: OAuthUseCase = Depends(get_oauth_use_case),
    ) -> RedirectResponse:
        apple_auth_url = await use_case.get_auth_url(OAuthProvider.APPLE, base_url=base_url)
        return RedirectResponse(url=apple_auth_url)

    # - MARK: Apple ID 토큰 로그인
    @staticmethod
    @router.post(
        AppleOauthRouterLabel.PREFIX,
        response_model=BaseResponse[LoginInfoDto],
        description="Apple ID 토큰을 통한 Apple 로그인",
    )
    async def apple_login(
            payload: AppleLoginRequest,
            use_case: OAuthUseCase = Depends(get_oauth_use_case),
    ) -> BaseResponse[LoginInfoDto]:
        result = await use_case.sign_in_with_apple(payload)
        return BaseResponse.ok(data=result)

    # - MARK: Apple OAuth 콜백
    @staticmethod
    @router.post(
        f"/{AppleOauthRouterLabel.PREFIX}/callback",
        include_in_schema=False,
        response_model=None,
        description="Apple OAuth 콜백 처리 (form_post)",
    )
    async def apple_callback(
            code: str | None = Form(None, description="인가 코드"),
            state: str | None = Form(None, description="상태값"),
            error: str | None = Form(None, description="에러 코드"),
            error_description: str | None = Form(None, description="에러 설명"),
            id_token: str | None = Form(None, description="ID 토큰"),
            user: str | None = Form(None, description="사용자 정보 (JSON 문자열)"),
            use_case: OAuthUseCase = Depends(get_oauth_use_case),
    ) -> RedirectResponse | BaseResponse[LoginInfoDto]:
        result = await use_case.handle_oauth_callback(
            provider=OAuthProvider.APPLE,
            code=code,
            error=error,
            error_description=error_description,
            id_token=id_token,
            user=user,
        )
        return result
