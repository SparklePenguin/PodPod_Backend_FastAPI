from typing_extensions import reveal_type
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.kakao_oauth_service import KakaoOauthService
from app.services.google_oauth_service import GoogleOauthService
from app.services.apple_oauth_service import AppleOauthService
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.services.artist_service import ArtistService
from app.services.oauth_service import OauthService


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
