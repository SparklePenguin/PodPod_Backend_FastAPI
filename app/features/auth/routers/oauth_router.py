from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse
from app.core.http_status import HttpStatus
from app.deps.database import get_session
from app.features.auth.services.apple_oauth_service import (
    AppleCallbackParam,
    AppleOauthService,
)
from app.features.auth.services.kakao_oauth_service import (
    KakaoCallBackParam,
    KakaoOauthService,
)

router = APIRouter()
security = HTTPBearer()


# - MARK: 카카오 OAuth 콜백
@router.get(
    "/kakao/callback",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "카카오 로그인 성공",
        },
    },
)
async def kakao_callback(
    code: Optional[str] = Query(None, description="인가 코드"),
    error: Optional[str] = Query(None, description="에러 코드"),
    error_description: Optional[str] = Query(None, description="에러 설명"),
    state: Optional[str] = Query(None, description="상태값"),
    session: AsyncSession = Depends(get_session),
):
    """카카오 OAuth 콜백 처리

    카카오 로그인 후 리다이렉트되는 콜백 엔드포인트입니다.
    인가 코드를 받아서 토큰을 발급하고 사용자 정보를 저장합니다.
    """
    params = KakaoCallBackParam(
        code=code,
        error=error,
        error_description=error_description,
        state=state,
    )
    service = KakaoOauthService(session)
    result = await service.handle_kakao_callback(params)
    # result는 SignInResponse이므로 model_dump 사용 가능
    if hasattr(result, "model_dump"):
        return BaseResponse.ok(data=result.model_dump(by_alias=True))
    else:
        return BaseResponse.ok(data=result)


# - MARK: Apple 콜백
@router.get(
    "/apple/callback",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "Apple 콜백 처리 성공",
        },
    },
)
async def apple_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    id_token: Optional[str] = None,
    user: Optional[str] = None,  # JSON 문자열로 전달됨
    session: AsyncSession = Depends(get_session),
):
    """Apple 콜백 처리 (안드로이드 웹뷰 콜백)"""
    # user 파라미터를 dict로 변환
    user_dict = None
    if user:
        try:
            import json

            user_dict = json.loads(user)
        except json.JSONDecodeError:
            user_dict = None

    callback_params = AppleCallbackParam(
        code=code,
        state=state,
        error=error,
        error_description=error_description,
        id_token=id_token,
        user=user_dict,
    )

    service = AppleOauthService(session)
    result = await service.handle_apple_callback(callback_params)
    # result는 RedirectResponse이므로 그대로 반환
    if isinstance(result, RedirectResponse):
        return result
    else:
        # SignInResponse인 경우
        if hasattr(result, "model_dump"):
            return BaseResponse.ok(data=result.model_dump(by_alias=True))
        else:
            return BaseResponse.ok(data=result)
