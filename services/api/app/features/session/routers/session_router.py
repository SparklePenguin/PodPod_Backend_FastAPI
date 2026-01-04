from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.service import get_session_use_case
from app.features.session.schemas import (
    LoginRequest,
    LogoutRequest,
    TokenRefreshRequest,
)
from app.features.session.use_cases.session_use_case import SessionUseCase
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter()
security = HTTPBearer()


# - MARK: 세션 생성 (로그인)
@router.post(
    "",
    response_model=BaseResponse[dict],
    description="세션 생성 (이메일 로그인 + 소셜 로그인 통합)",
)
async def create_session(
    login_data: LoginRequest,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    result = await use_case.login(login_data)
    return BaseResponse.ok(data=result.model_dump(by_alias=True))


# - MARK: 세션 삭제 (로그아웃)
@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    description="로그아웃 (세션 삭제, 리프레시 토큰 무효화, FCM 토큰 삭제)",
    dependencies=[Depends(security)],
)
async def delete_session(
    logout_data: LogoutRequest,
    current_user_id: int = Depends(get_current_user_id),
    token: HTTPAuthorizationCredentials = Depends(security),
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    await use_case.logout(
        access_token=token.credentials,
        refresh_token=logout_data.refresh_token,
        user_id=current_user_id,
    )
    return BaseResponse.ok(http_status=status.HTTP_204_NO_CONTENT)


# - MARK: 토큰 갱신
@router.put("", response_model=BaseResponse[dict], description="토큰 갱신")
async def refresh_session(
    refresh_data: TokenRefreshRequest,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    from app.core.session import (
        TokenBlacklistedError,
        TokenDecodeError,
        TokenExpiredError,
        TokenInvalidError,
    )

    try:
        credential = await use_case.refresh_token(refresh_data.refresh_token)
        return BaseResponse.ok(data=credential.model_dump(by_alias=True))
    except (
        TokenExpiredError,
        TokenInvalidError,
        TokenDecodeError,
        TokenBlacklistedError,
    ) as e:
        return BaseResponse.error(
            error_key="TOKEN_INVALID",
            error_code=1002,
            http_status=status.HTTP_401_UNAUTHORIZED,
            message_ko=e.message,
            message_en=e.message,
        )
    except Exception as e:
        return BaseResponse.error(
            error_key="TOKEN_REFRESH_FAILED",
            error_code=5001,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=f"토큰 갱신 실패: {str(e)}",
            message_en=f"Token refresh failed: {str(e)}",
        )
