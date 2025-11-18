from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math
from app.crud.artist_suggestion import ArtistSuggestionCRUD
from app.schemas.artist_suggestion import (
    ArtistSuggestionCreateRequest,
    ArtistSuggestionDto,
    ArtistSuggestionRankingDto,
)
from app.schemas.common import PageDto
from app.core.logging_config import get_logger
from app.core.exceptions import BusinessException

logger = get_logger("artist_suggestion_service")


class ArtistSuggestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = ArtistSuggestionCRUD(db)

    async def create_suggestion(
        self, request: ArtistSuggestionCreateRequest, user_id: int
    ) -> ArtistSuggestionDto:
        """아티스트 제안 생성"""
        logger.info(
            f"아티스트 제안 생성 요청: {request.artist_name} (user_id: {user_id})"
        )

        # 중복 체크
        is_duplicate = await self.crud.check_duplicate_suggestion(
            request.artist_name, user_id
        )
        if is_duplicate:
            raise BusinessException(
                error_code="DUPLICATE_ARTIST_SUGGESTION",
                message_ko=f"'{request.artist_name}' 아티스트에 대한 제안을 이미 하셨습니다.",
                status_code=409,
            )

        suggestion = await self.crud.create_suggestion(
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
        suggestion = await self.crud.get_suggestion_by_id(suggestion_id)
        if not suggestion:
            return None

        return ArtistSuggestionDto.model_validate(suggestion)

    async def get_suggestions(
        self, page: int = 1, size: int = 20
    ) -> PageDto[ArtistSuggestionDto]:
        """제안 목록 조회"""
        suggestions, total_count = await self.crud.get_suggestions(page, size)

        suggestion_dtos = []
        for suggestion in suggestions:
            suggestion_dto = ArtistSuggestionDto.model_validate(suggestion)
            suggestion_dtos.append(suggestion_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[ArtistSuggestionDto](
            items=suggestion_dtos,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def get_artist_ranking(
        self, page: int = 1, limit: int = 20
    ) -> PageDto[ArtistSuggestionRankingDto]:
        """아티스트별 요청 순위 조회"""
        logger.info(f"아티스트 순위 조회 요청 (page: {page}, limit: {limit})")

        rankings, total_count = await self.crud.get_artist_ranking(page, limit)

        ranking_dtos = []
        for ranking in rankings:
            ranking_dto = ArtistSuggestionRankingDto(
                artist_name=ranking["artist_name"], count=ranking["count"]
            )
            ranking_dtos.append(ranking_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

        return PageDto[ArtistSuggestionRankingDto](
            items=ranking_dtos,
            current_page=page,
            size=limit,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def get_suggestions_by_artist_name(
        self, artist_name: str, page: int = 1, size: int = 20
    ) -> PageDto[ArtistSuggestionDto]:
        """특정 아티스트명으로 제안 목록 조회"""
        logger.info(f"특정 아티스트 제안 조회: {artist_name}")

        suggestions, total_count = await self.crud.get_suggestions_by_artist_name(
            artist_name, page, size
        )

        suggestion_dtos = []
        for suggestion in suggestions:
            suggestion_dto = ArtistSuggestionDto.model_validate(suggestion)
            suggestion_dtos.append(suggestion_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[ArtistSuggestionDto](
            items=suggestion_dtos,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
