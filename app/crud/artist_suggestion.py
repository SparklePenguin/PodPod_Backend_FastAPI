from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.artist_suggestion import ArtistSuggestion


class ArtistSuggestionCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_suggestion(
        self,
        artist_name: str,
        reason: Optional[str] = None,
        email: Optional[str] = None,
    ) -> ArtistSuggestion:
        """아티스트 제안 생성"""
        suggestion = ArtistSuggestion(
            artist_name=artist_name, reason=reason, email=email
        )
        self.db.add(suggestion)
        await self.db.commit()
        await self.db.refresh(suggestion)
        return suggestion

    async def get_suggestion_by_id(
        self, suggestion_id: int
    ) -> Optional[ArtistSuggestion]:
        """ID로 제안 조회"""
        query = select(ArtistSuggestion).where(ArtistSuggestion.id == suggestion_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_suggestions(
        self, page: int = 1, size: int = 20
    ) -> Tuple[List[ArtistSuggestion], int]:
        """제안 목록 조회 (페이지네이션)"""
        offset = (page - 1) * size

        # 제안 목록 조회
        query = (
            select(ArtistSuggestion)
            .order_by(desc(ArtistSuggestion.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        suggestions = result.scalars().all()

        # 전체 개수 조회
        count_query = select(func.count(ArtistSuggestion.id))
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        return suggestions, total_count

    async def get_artist_ranking(self, limit: int = 50) -> List[dict]:
        """아티스트별 요청 순위 조회"""
        query = (
            select(
                ArtistSuggestion.artist_name,
                func.count(ArtistSuggestion.id).label("count"),
            )
            .group_by(ArtistSuggestion.artist_name)
            .order_by(desc("count"))
            .limit(limit)
        )
        result = await self.db.execute(query)

        rankings = []
        for row in result:
            rankings.append({"artist_name": row.artist_name, "count": row.count})

        return rankings

    async def get_suggestions_by_artist_name(
        self, artist_name: str, page: int = 1, size: int = 20
    ) -> Tuple[List[ArtistSuggestion], int]:
        """특정 아티스트명으로 제안 목록 조회"""
        offset = (page - 1) * size

        # 특정 아티스트 제안 목록 조회
        query = (
            select(ArtistSuggestion)
            .where(ArtistSuggestion.artist_name == artist_name)
            .order_by(desc(ArtistSuggestion.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        suggestions = result.scalars().all()

        # 해당 아티스트의 전체 개수 조회
        count_query = select(func.count(ArtistSuggestion.id)).where(
            ArtistSuggestion.artist_name == artist_name
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        return suggestions, total_count
