from fastapi import APIRouter, Query, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import Optional
from app.services.kakao_oauth_service import KakaoOauthService, KakaoCallBackParam
from app.services.apple_oauth_service import AppleOauthService, AppleCallbackParam
from app.schemas.common import SuccessResponse, ErrorResponse
from app.api.deps import get_kakao_oauth_service, get_apple_oauth_service

router = APIRouter()
security = HTTPBearer()


# - MARK: 카카오 OAuth 콜백
@router.get(
    "/kakao/callback",
    response_model=SuccessResponse,  # 응답 모델 명시
    responses={
        200: {"model": SuccessResponse, "description": "카카오 로그인 성공"},
        400: {"model": ErrorResponse, "description": "카카오 인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def kakao_callback(
    code: Optional[str] = Query(None, description="인가 코드"),
    error: Optional[str] = Query(None, description="에러 코드"),
    error_description: Optional[str] = Query(None, description="에러 설명"),
    state: Optional[str] = Query(None, description="상태값"),
    kakao_oauth_service: KakaoOauthService = Depends(get_kakao_oauth_service),
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
    return await kakao_oauth_service.handle_kakao_callback(params)


# - MARK: Apple 콜백
@router.get(
    "/apple/callback",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "Apple 콜백 처리 성공"},
        400: {"model": ErrorResponse, "description": "Apple 콜백 처리 실패"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def apple_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    id_token: Optional[str] = None,
    user: Optional[str] = None,  # JSON 문자열로 전달됨
    apple_oauth_service: AppleOauthService = Depends(get_apple_oauth_service),
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

    return await apple_oauth_service.handle_apple_callback(callback_params)
