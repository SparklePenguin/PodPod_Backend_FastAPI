from typing import Optional
from typing_extensions import reveal_type
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from app.core.database import get_db
from app.core.config import settings
from app.features.auth.services.kakao_oauth_service import KakaoOauthService
from app.features.auth.services.google_oauth_service import GoogleOauthService
from app.features.auth.services.apple_oauth_service import AppleOauthService
from app.features.users.services import UserService
from app.features.auth.services.session_service import SessionService
from app.features.artists.services.artist_service import ArtistService
from app.features.auth.services.oauth_service import OauthService

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(db)


def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OauthService:
    return OauthService(db)


def get_kakao_oauth_service(db: AsyncSession = Depends(get_db)) -> KakaoOauthService:
    return KakaoOauthService(db)


def get_google_oauth_service(db: AsyncSession = Depends(get_db)) -> GoogleOauthService:
    return GoogleOauthService(db)


def get_apple_oauth_service(db: AsyncSession = Depends(get_db)) -> AppleOauthService:
    return AppleOauthService(db)


def get_artist_service(db: AsyncSession = Depends(get_db)) -> ArtistService:
    return ArtistService(db)


async def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """토큰에서 user_id 추출"""
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        # JWT의 sub 필드는 문자열이므로 정수로 변환
        user_id = int(user_id_str)
        return user_id
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_user_id_optional(
    token: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[int]:
    """토큰에서 user_id 추출 (선택사항)"""
    if token is None:
        return None
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        # JWT의 sub 필드는 문자열이므로 정수로 변환
        user_id = int(user_id_str)
        return user_id
    except (JWTError, ValueError):
        return None
