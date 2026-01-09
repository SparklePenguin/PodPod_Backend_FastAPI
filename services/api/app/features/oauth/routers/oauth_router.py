"""OAuth Router"""

from app.common.schemas import BaseResponse
from app.deps.providers import get_oauth_use_case
from app.deps.redis import get_redis
from app.features.auth.schemas import LoginInfoDto
from app.features.oauth.schemas import (
    AppleLoginRequest,
    GoogleLoginRequest,
    KakaoLoginRequest,
    OAuthProvider,
)
from app.features.oauth.use_cases.oauth_use_case import OAuthUseCase
from fastapi import APIRouter, Depends, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

router = APIRouter(prefix="/oauth", tags=["oauth"])
security = HTTPBearer()


# - MARK: Kakao 로그인 시작
@router.get(
    "/kakao/login",
    response_class=RedirectResponse,
    status_code=307,
    description="카카오 로그인 시작 - 카카오 인증 페이지로 리다이렉트",
)
async def kakao_login_web(
    use_case: OAuthUseCase = Depends(get_oauth_use_case),
) -> RedirectResponse:
    kakao_auth_url = await use_case.get_auth_url(OAuthProvider.KAKAO)
    return RedirectResponse(url=kakao_auth_url)


# - MARK: Kakao OAuth 콜백
@router.get(
    "/kakao/callback",
    include_in_schema=False,
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


# - MARK: Kakao 액세스 토큰 로그인
@router.post(
    "/kakao",
    response_model=BaseResponse[LoginInfoDto],
    description="카카오 액세스 토큰을 통한 카카오 로그인",
)
async def kakao_login(
    request: KakaoLoginRequest,
    use_case: OAuthUseCase = Depends(get_oauth_use_case),
) -> BaseResponse[LoginInfoDto]:
    result = await use_case.sign_in_with_kakao(request)
    return BaseResponse.ok(data=result)


# - MARK: Naver 로그인 시작
@router.get(
    "/naver/login",
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


# - MARK: Naver OAuth 콜백
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


# - MARK: Google 로그인 시작
@router.get(
    "/google/login",
    response_class=RedirectResponse,
    status_code=307,
    description="구글 로그인 시작 - 구글 인증 페이지로 리다이렉트",
)
async def google_login_web(
    use_case: OAuthUseCase = Depends(get_oauth_use_case),
) -> RedirectResponse:
    google_auth_url = await use_case.get_auth_url(OAuthProvider.GOOGLE)
    return RedirectResponse(url=google_auth_url)


# - MARK: Google OAuth 콜백
@router.get(
    "/google/callback",
    include_in_schema=False,
    description="구글 OAuth 콜백의 인가코드를 통한 구글 로그인",
)
async def google_callback(
    code: str | None = Query(None, description="인가 코드"),
    state: str | None = Query(None, description="상태값"),
    error_description: str | None = Query(None, description="에러 설명"),
    error: str | None = Query(None, description="에러 코드"),
    use_case: OAuthUseCase = Depends(get_oauth_use_case),
) -> BaseResponse[LoginInfoDto]:
    result = await use_case.handle_oauth_callback(
        provider=OAuthProvider.GOOGLE,
        code=code,
        error=error,
        error_description=error_description,
    )
    return BaseResponse.ok(data=result)


# - MARK: Google ID 토큰 로그인
@router.post(
    "/google",
    response_model=BaseResponse[LoginInfoDto],
    description="구글 ID 토큰을 통한 구글 로그인",
)
async def google_login(
    payload: GoogleLoginRequest,
    use_case: OAuthUseCase = Depends(get_oauth_use_case),
) -> BaseResponse[LoginInfoDto]:
    result = await use_case.sign_in_with_google(payload)
    return BaseResponse.ok(data=result)


# - MARK: Apple 로그인 시작
@router.get(
    "/apple/login",
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


# - MARK: Apple OAuth 콜백
@router.post(
    "/apple/callback",
    include_in_schema=False,
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


# - MARK: Apple ID 토큰 로그인
@router.post(
    "/apple",
    response_model=BaseResponse[LoginInfoDto],
    description="Apple ID 토큰을 통한 Apple 로그인",
)
async def apple_login(
    payload: AppleLoginRequest,
    use_case: OAuthUseCase = Depends(get_oauth_use_case),
) -> BaseResponse[LoginInfoDto]:
    result = await use_case.sign_in_with_apple(payload)
    return BaseResponse.ok(data=result)
