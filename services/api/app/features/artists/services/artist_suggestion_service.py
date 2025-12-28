from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PageDto
from app.core.exceptions import BusinessException
from app.features.artists.repositories.artist_suggestion_repository import (
    ArtistSuggestionRepository,
)
from app.features.artists.schemas import (
    ArtistSuggestionCreateRequest,
    ArtistSuggestionDto,
    ArtistSuggestionRankingDto,
)


class ArtistSuggestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.artist_sugg_repo = ArtistSuggestionRepository(db)

    async def create_suggestion(
        self, request: ArtistSuggestionCreateRequest, user_id: int
    ) -> ArtistSuggestionDto:
        """아티스트 제안 생성"""
        # 중복 체크
        is_duplicate = await self.artist_sugg_repo.check_duplicate_suggestion(
            request.artist_name, user_id
        )
        if is_duplicate:
            raise BusinessException(
                error_code="DUPLICATE_ARTIST_SUGGESTION",
                message_ko=f"'{request.artist_name}' 아티스트에 대한 제안을 이미 하셨습니다.",
                status_code=409,
            )

        suggestion = await self.artist_sugg_repo.create_suggestion(
            artist_name=request.artist_name,
            reason=request.reason,
            email=request.email,
            user_id=user_id,
        )

        return ArtistSuggestionDto.model_validate(suggestion)

    async def get_suggestion_by_id(
        self, suggestion_id: int
    ) -> Optional[ArtistSuggestionDto]:
        """ID로 제안 조회"""
        suggestion = await self.artist_sugg_repo.get_suggestion_by_id(suggestion_id)
        if not suggestion:
            return None

        return ArtistSuggestionDto.model_validate(suggestion)

    async def get_suggestions(
        self, page: int = 1, size: int = 20
    ) -> PageDto[ArtistSuggestionDto]:
        """제안 목록 조회"""
        suggestions, total_count = await self.artist_sugg_repo.get_suggestions(
            page, size
        )

        suggestion_dtos = [
            ArtistSuggestionDto.model_validate(suggestion) for suggestion in suggestions
        ]

        return PageDto.create(
            items=suggestion_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    async def get_artist_ranking(
        self, page: int = 1, limit: int = 20
    ) -> PageDto[ArtistSuggestionRankingDto]:
        """아티스트별 요청 순위 조회"""
        rankings, total_count = await self.artist_sugg_repo.get_artist_ranking(
            page, limit
        )

        ranking_dtos = [
            ArtistSuggestionRankingDto(
                artist_name=ranking["artist_name"], count=ranking["count"]
            )
            for ranking in rankings
        ]

        return PageDto.create(
            items=ranking_dtos,
            page=page,
            size=limit,
            total_count=total_count,
        )

    async def get_suggestions_by_artist_name(
        self, artist_name: str, page: int = 1, size: int = 20
    ) -> PageDto[ArtistSuggestionDto]:
        """특정 아티스트명으로 제안 목록 조회"""

        (
            suggestions,
            total_count,
        ) = await self.artist_sugg_repo.get_suggestions_by_artist_name(
            artist_name, page, size
        )

        suggestion_dtos = [
            ArtistSuggestionDto.model_validate(suggestion) for suggestion in suggestions
        ]

        return PageDto.create(
            items=suggestion_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )
