from typing_extensions import reveal_type
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.kakao_oauth_service import KakaoOauthService
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.services.artist_service import ArtistService


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(db)


def get_kakao_oauth_service() -> KakaoOauthService:
    return KakaoOauthService(
        user_service=get_user_service(),
        session_service=get_session_service(),
    )


def get_artist_service(db: AsyncSession = Depends(get_db)) -> ArtistService:
    return ArtistService(db)
