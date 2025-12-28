from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.artists.services.artist_schedule_service import ArtistScheduleService
from app.features.artists.services.artist_service import ArtistService
from app.features.artists.services.artist_suggestion_service import (
    ArtistSuggestionService,
)


def get_artist_service(db: AsyncSession = Depends(get_session)) -> ArtistService:
    return ArtistService(db)


def get_artist_schedule_service(
    db: AsyncSession = Depends(get_session),
) -> ArtistScheduleService:
    return ArtistScheduleService(db)


def get_artist_suggestion_service(
    db: AsyncSession = Depends(get_session),
) -> ArtistSuggestionService:
    return ArtistSuggestionService(db)
