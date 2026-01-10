"""아티스트 제안 관련 Use Cases"""

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
from app.features.artists.services.artist_dto_service import ArtistDtoService
from sqlalchemy.ext.asyncio import AsyncSession


class CreateArtistSuggestionUseCase:
    """아티스트 제안 생성 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.suggestion_repo = ArtistSuggestionRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(
        self, request: ArtistSuggestionCreateRequest, user_id: int
    ) -> ArtistSuggestionDto:
        """아티스트 제안 생성"""
        # 중복 체크
        is_duplicate = await self.suggestion_repo.check_duplicate_suggestion(
            request.artist_name, user_id
        )
        if is_duplicate:
            raise BusinessException(
                error_code="DUPLICATE_ARTIST_SUGGESTION",
                message_ko=f"'{request.artist_name}' 아티스트에 대한 제안을 이미 하셨습니다.",
                status_code=409,
            )

        # Repository에서 제안 객체 생성 (커밋 없이)
        suggestion = await self.suggestion_repo.create_suggestion_without_commit(
            artist_name=request.artist_name,
            reason=request.reason,
            email=request.email,
            user_id=user_id,
        )

        # Use Case에서 커밋 관리
        await self._session.commit()
        await self._session.refresh(suggestion)

        return self.dto_service.to_suggestion_dto(suggestion)


class GetSuggestionByIdUseCase:
    """ID로 제안 조회 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.suggestion_repo = ArtistSuggestionRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(self, suggestion_id: int) -> ArtistSuggestionDto | None:
        """ID로 제안 조회"""
        suggestion = await self.suggestion_repo.get_suggestion_by_id(suggestion_id)
        if not suggestion:
            return None

        return self.dto_service.to_suggestion_dto(suggestion)


class GetSuggestionsUseCase:
    """제안 목록 조회 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.suggestion_repo = ArtistSuggestionRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(
        self, page: int = 1, size: int = 20
    ) -> PageDto[ArtistSuggestionDto]:
        """제안 목록 조회"""
        suggestions, total_count = await self.suggestion_repo.get_suggestions(
            page, size
        )

        suggestion_dtos = self.dto_service.to_suggestion_dtos(suggestions)

        return PageDto.create(
            items=suggestion_dtos, page=page, size=size, total_count=total_count
        )


class GetArtistRankingUseCase:
    """아티스트별 요청 순위 조회 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.suggestion_repo = ArtistSuggestionRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(
        self, page: int = 1, limit: int = 20
    ) -> PageDto[ArtistSuggestionRankingDto]:
        """아티스트별 요청 순위 조회"""
        rankings, total_count = await self.suggestion_repo.get_artist_ranking(
            page, limit
        )

        ranking_dtos = self.dto_service.to_ranking_dtos(rankings)

        return PageDto.create(
            items=ranking_dtos, page=page, size=limit, total_count=total_count
        )


class GetSuggestionsByArtistNameUseCase:
    """특정 아티스트명으로 제안 목록 조회 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.suggestion_repo = ArtistSuggestionRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(
        self, artist_name: str, page: int = 1, size: int = 20
    ) -> PageDto[ArtistSuggestionDto]:
        """특정 아티스트명으로 제안 목록 조회"""
        (
            suggestions,
            total_count,
        ) = await self.suggestion_repo.get_suggestions_by_artist_name(
            artist_name, page, size
        )

        suggestion_dtos = self.dto_service.to_suggestion_dtos(suggestions)

        return PageDto.create(
            items=suggestion_dtos, page=page, size=size, total_count=total_count
        )
