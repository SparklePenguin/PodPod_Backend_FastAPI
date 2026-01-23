from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

from app.common.schemas import BaseResponse
from app.deps.providers import get_oauth_use_case
from app.deps.redis import get_redis
from app.features.auth.schemas import LoginInfoDto
from app.features.oauth.schemas import (
    OAuthProvider,
)
from app.features.oauth.use_cases.oauth_use_case import OAuthUseCase
from ._base import OAuthController

security = HTTPBearer()


class NaverOauthRouter:
    router = APIRouter(
        prefix=OAuthController.PREFIX,
        tags=[OAuthController.TAG]
    )

    @staticmethod
    @router.get(
        "/naver/login",
        deprecated=True,
        response_class=RedirectResponse,
        status_code=307,
        description="네이버 로그인 시작 - 네이버 인증 페이지로 리다이렉트",
    )
    async def naver_login_web(
            redis: Redis = Depends(get_redis),
            use_case: OAuthUseCase = Depends(get_oauth_use_case),
    ) -> RedirectResponse:
        naver_auth_url = await use_case.get_auth_url(OAuthProvider.NAVER, redis)
        return RedirectResponse(url=naver_auth_url)

    @staticmethod
    @router.get(
        "/naver/callback",
        include_in_schema=False,
        description="네이버 OAuth 콜백의 인가코드를 통한 네이버 로그인",
    )
    async def naver_callback(
            code: str | None = Query(None, description="인가 코드"),
            state: str | None = Query(None, description="상태값"),
            error_description: str | None = Query(None, description="에러 설명"),
            error: str | None = Query(None, description="에러 코드"),
            redis: Redis = Depends(get_redis),
            use_case: OAuthUseCase = Depends(get_oauth_use_case),
    ) -> BaseResponse[LoginInfoDto]:
        result = await use_case.handle_oauth_callback(
            provider=OAuthProvider.NAVER,
            code=code,
            state=state,
            error=error,
            error_description=error_description,
            redis=redis,
        )
        return BaseResponse.ok(data=result)
