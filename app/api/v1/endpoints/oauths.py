from fastapi import APIRouter, Query, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
from app.services.kakao_oauth_service import KakaoOauthService, KakaoCallBackParam
from app.schemas.common import SuccessResponse, ErrorResponse

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
):
    """카카오 OAuth 콜백 처리

    카카오 로그인 후 리다이렉트되는 콜백 엔드포인트입니다.
    인가 코드를 받아서 토큰을 발급하고 사용자 정보를 저장합니다.
    """
    kakao_service = KakaoOauthService()
    params = KakaoCallBackParam(
        code=code,
        error=error,
        error_description=error_description,
        state=state,
    )
    return await kakao_service.handle_kakao_callback(params)  # await 추가
