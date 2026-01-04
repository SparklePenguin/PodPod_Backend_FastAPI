from app.core.session import create_access_token, verify_refresh_token
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

security = HTTPBearer()
refresh_token_header = APIKeyHeader(
    name="X-Refresh-Token", auto_error=False, description="Refresh Token (Optional)"
)


async def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    refresh_token: str | None = Depends(refresh_token_header),
) -> int:
    """
    Access Token으로 사용자 ID 조회
    Access Token 만료 시 Refresh Token으로 자동 갱신 시도
    """
    access_token = credentials.credentials

    try:
        # Access Token 검증
        payload = jwt.decode(access_token, settings.secret_key, algorithms=["HS256"])
        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Missing subject")
        return int(subject)

    except JWTError as exc:
        # Access Token 만료 시 Refresh Token으로 갱신 시도
        if refresh_token:
            try:
                # Refresh Token 검증 및 user_id 추출 (Redis 확인 포함)
                user_id = await verify_refresh_token(refresh_token)

                # 새 Access Token 생성
                new_access_token = create_access_token(user_id)

                # Response Header에 새 토큰 추가 (미들웨어에서 처리)
                request.state.new_access_token = new_access_token

                return user_id

            except (HTTPException, TypeError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Access token expired and refresh token is invalid",
                ) from exc

        # Refresh Token이 없으면 그냥 실패
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
