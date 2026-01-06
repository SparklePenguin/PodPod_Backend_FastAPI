from app.core.config import settings
from app.core.session import create_access_token, verify_refresh_token
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()


async def get_refresh_token(
    x_refresh_token: str | None = Header(
        None, alias="X-Refresh-Token", description="Refresh Token (Optional)"
    ),
) -> str | None:
    """Refresh Token 헤더에서 추출"""
    return x_refresh_token


async def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    refresh_token: str | None = Depends(get_refresh_token),
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
