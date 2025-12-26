from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.artists.services.artist_service import ArtistService


def get_artist_service(db: AsyncSession = Depends(get_session)) -> ArtistService:
    return ArtistService(db)
