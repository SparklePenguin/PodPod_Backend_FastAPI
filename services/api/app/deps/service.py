from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.artists.services.artist_schedule_service import ArtistScheduleService
from app.features.artists.services.artist_service import ArtistService
from app.features.artists.services.artist_suggestion_service import (
    ArtistSuggestionService,
)
from app.features.oauth.services.oauth_service import OAuthService


def get_artist_service(session: AsyncSession = Depends(get_session)) -> ArtistService:
    return ArtistService(session)


def get_artist_schedule_service(
    session: AsyncSession = Depends(get_session),
) -> ArtistScheduleService:
    return ArtistScheduleService(session)


def get_artist_suggestion_service(
    session: AsyncSession = Depends(get_session),
) -> ArtistSuggestionService:
    return ArtistSuggestionService(session)


def get_oauth_service(session: AsyncSession = Depends(get_session)) -> OAuthService:
    return OAuthService(session)
