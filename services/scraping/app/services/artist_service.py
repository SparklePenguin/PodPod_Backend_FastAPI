from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.artist_repository import ArtistRepository


class ArtistService:
    def __init__(self, db: AsyncSession):
        self.artist_crud = ArtistRepository(db)

    # - MARK: (내부용) BLIP+MVP 병합 동기화
    async def sync_blip_and_mvp(self) -> dict:
        """BLIP 전체 데이터와 MVP 이름 목록을 병합하여 DB에 동기화"""
        return await self.artist_crud.sync_from_blip_and_mvp()
