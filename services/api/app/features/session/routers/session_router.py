from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse
from app.core.http_status import HttpStatus
from app.deps.auth import get_current_user_id
from app.deps.database import get_session
from app.features.session.schemas import LoginRequest, TokenRefreshRequest
from app.features.session.services.session_service import SessionService

router = APIRouter()
security = HTTPBearer()


@router.post(
    "",
    response_model=BaseResponse[dict],
    description="세션 생성 (이메일 로그인 + 소셜 로그인 통합)",
)
async def create_session(
    login_data: LoginRequest, session: AsyncSession = Depends(get_session)
):
    service = SessionService(session)
    result = await service.login(login_data)
    return BaseResponse.ok(data=result.model_dump(by_alias=True))


@router.delete(
    "",
    status_code=HttpStatus.NO_CONTENT,
    description="로그아웃 (세션 삭제 및 FCM 토큰 삭제)",
    dependencies=[Depends(security)],
)
async def delete_session(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    token: HTTPAuthorizationCredentials = Depends(security),
):
    service = SessionService(session)
    await service.logout(token.credentials, current_user_id)
    return BaseResponse.ok(http_status=HttpStatus.NO_CONTENT)


@router.put("", response_model=BaseResponse[dict], description="토큰 갱신")
async def refresh_session(
    refresh_data: TokenRefreshRequest, session: AsyncSession = Depends(get_session)
):
    from app.core.security import (
        TokenBlacklistedError,
        TokenDecodeError,
        TokenExpiredError,
        TokenInvalidError,
    )

    try:
        service = SessionService(session)
        credential = await service.refresh_token(refresh_data.refresh_token)
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
            http_status=HttpStatus.UNAUTHORIZED,
            message_ko=e.message,
            message_en=e.message,
        )
    except Exception as e:
        return BaseResponse.error(
            error_key="TOKEN_REFRESH_FAILED",
            error_code=5001,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=f"토큰 갱신 실패: {str(e)}",
            message_en=f"Token refresh failed: {str(e)}",
        )
