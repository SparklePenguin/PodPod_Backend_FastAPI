"""Pod Query Use Case - 파티 조회 비즈니스 로직

파티 목록 조회, 검색, 상세 조회 등 읽기 전용 작업을 담당합니다.
"""

from datetime import date
from typing import TYPE_CHECKING

from app.common.schemas import PageDto
from app.features.pods.exceptions import (
    InvalidDateException,
    InvalidPodTypeException,
    PodNotFoundException,
    SelectedArtistIdRequiredException,
)
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.schemas import PodDetailDto
from app.features.pods.schemas.pod_schemas import PodDto
from app.features.pods.services.pod_enrichment_service import PodEnrichmentService
from app.features.users.exceptions import UserNotFoundException
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.features.follow.use_cases.follow_use_case import FollowUseCase


class PodQueryUseCase:
    """파티 조회 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        pod_repo: PodRepository,
        user_repo: UserRepository,
        enrichment_service: PodEnrichmentService,
        follow_use_case: "FollowUseCase | None" = None,
    ):
        self._session = session
        self._pod_repo = pod_repo
        self._user_repo = user_repo
        self._enrichment_service = enrichment_service
        self._follow_use_case = follow_use_case

    # MARK: - 파티 상세 조회
    async def get_pod_detail(
        self, pod_id: int, user_id: int | None = None
    ) -> PodDetailDto:
        """파티 상세 정보 조회"""
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        return await self._enrichment_service.enrich(pod, user_id)

    # MARK: - 인기 파티 조회
    async def get_trending_pods(
        self, user_id: int, selected_artist_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """
        요즘 인기 있는 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 최근 7일 이내 인기도 기반 정렬
        - 페이지네이션 지원
        """
        pods = await self._pod_repo.get_trending_pods(
            user_id, selected_artist_id, page, size
        )

        pod_dtos = await self._enrichment_service.convert_batch(
            pods, user_id, include_applications=False, include_reviews=False
        )

        total_count = len(pod_dtos)

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # MARK: - 마감 임박 파티 조회
    async def get_closing_soon_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDto]:
        """
        마감 직전 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 에디터가 설정한 지역 (선택사항)
        - 24시간 이내 마감 모임 우선 정렬
        - 페이지네이션 지원
        """
        pods = await self._pod_repo.get_closing_soon_pods(
            user_id, selected_artist_id, location, page, size
        )

        pod_dtos = await self._enrichment_service.convert_batch(
            pods, user_id, include_applications=False, include_reviews=False
        )

        total_count = len(pod_dtos)

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # MARK: - 히스토리 기반 파티 조회
    async def get_history_based_pods(
        self, user_id: int, selected_artist_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """
        우리 만난적 있어요 - 히스토리 기반 파티 조회
        - 이전에 함께 파티한 사용자의 새 파티
        - 페이지네이션 지원
        """
        pods = await self._pod_repo.get_history_based_pods(
            user_id, selected_artist_id, page, size
        )

        pod_dtos = await self._enrichment_service.convert_batch(
            pods, user_id, include_applications=False, include_reviews=False
        )

        total_count = len(pod_dtos)

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # MARK: - 인기 카테고리 파티 조회
    async def get_popular_categories_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDto]:
        """
        인기 카테고리 파티 조회
        - 인기 카테고리 기반 파티 목록
        - 페이지네이션 지원
        """
        pods = await self._pod_repo.get_popular_categories_pods(
            user_id, selected_artist_id, location, page, size
        )

        pod_dtos = await self._enrichment_service.convert_batch(
            pods, user_id, include_applications=False, include_reviews=False
        )

        total_count = len(pod_dtos)

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # MARK: - 사용자 파티 조회
    async def get_user_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """사용자가 개설한 파티 목록 조회"""
        result = await self._pod_repo.get_user_pods(user_id, page, size)

        pod_dtos = await self._enrichment_service.convert_batch(
            result["items"], user_id, include_applications=False, include_reviews=False
        )

        return PageDto.create(
            items=pod_dtos,
            page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
        )

    # MARK: - 파티 검색
    async def search_pods(
        self,
        user_id: int | None = None,
        title: str | None = None,
        main_category: str | None = None,
        sub_category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        location: list[str | None] | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDto]:
        """파티 검색"""
        result = await self._pod_repo.search_pods(
            query=title or "",
            main_category=main_category,
            sub_categories=[sub_category] if sub_category else None,
            start_date=start_date,
            end_date=end_date,
            location=location[0] if location and len(location) > 0 else None,
            page=page,
            size=size,
        )

        pod_dtos = await self._enrichment_service.convert_batch(
            result["items"], user_id, include_applications=False, include_reviews=False
        )

        return PageDto.create(
            items=pod_dtos,
            page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
        )

    # MARK: - 참여한 파티 조회
    async def get_user_joined_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """사용자가 참여한 파티 목록 조회"""
        result = await self._pod_repo.get_user_joined_pods(user_id, page, size)

        pod_dtos = await self._enrichment_service.convert_batch(
            result["items"], user_id, include_applications=False, include_reviews=False
        )

        return PageDto.create(
            items=pod_dtos,
            page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
        )

    # MARK: - 좋아요한 파티 조회
    async def get_user_liked_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """사용자가 좋아요한 파티 목록 조회"""
        result = await self._pod_repo.get_user_liked_pods(user_id, page, size)

        pod_dtos = await self._enrichment_service.convert_batch(
            result["items"], user_id, include_applications=False, include_reviews=False
        )

        return PageDto.create(
            items=pod_dtos,
            page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
        )

    # MARK: - 타입별 파티 목록 조회
    async def get_pods_by_type(
        self,
        user_id: int,
        pod_type: str,
        selected_artist_id: int | None = None,
        location: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[PageDto[PodDto], str, str]:
        """파티 목록 조회 (타입별 라우팅)

        Returns:
            tuple[PageDto[PodDto], message_ko, message_en]: 파티 목록과 메시지
        """
        # 전체 파티 목록 타입들 (selected_artist_id 필수)
        if pod_type == "trending":
            if selected_artist_id is None:
                raise SelectedArtistIdRequiredException(pod_type)
            pods = await self.get_trending_pods(user_id, selected_artist_id, page, size)
            return (
                pods,
                "인기 파티 목록을 조회했습니다.",
                "Successfully retrieved trending pods.",
            )

        elif pod_type == "closing-soon":
            if selected_artist_id is None:
                raise SelectedArtistIdRequiredException(pod_type)
            pods = await self.get_closing_soon_pods(
                user_id, selected_artist_id, location, page, size
            )
            return (
                pods,
                "마감 직전 파티 목록을 조회했습니다.",
                "Successfully retrieved closing soon pods.",
            )

        elif pod_type == "history-based":
            if selected_artist_id is None:
                raise SelectedArtistIdRequiredException(pod_type)
            pods = await self.get_history_based_pods(
                user_id, selected_artist_id, page, size
            )
            return (
                pods,
                "우리 만난적 있어요 파티 목록을 조회했습니다.",
                "Successfully retrieved history-based pods.",
            )

        elif pod_type == "popular-category":
            if selected_artist_id is None:
                raise SelectedArtistIdRequiredException(pod_type)
            pods = await self.get_popular_categories_pods(
                user_id, selected_artist_id, location, page, size
            )
            return (
                pods,
                "인기 카테고리 파티 목록을 조회했습니다.",
                "Successfully retrieved popular category pods.",
            )

        # 사용자별 파티 목록 타입들
        elif pod_type == "joined":
            pods = await self.get_user_joined_pods(user_id, page, size)
            return (
                pods,
                "내가 참여한 파티 목록을 조회했습니다.",
                "Successfully retrieved my joined pods.",
            )

        elif pod_type == "liked":
            pods = await self.get_user_liked_pods(user_id, page, size)
            return (
                pods,
                "내가 저장한 파티 목록을 조회했습니다.",
                "Successfully retrieved my liked pods.",
            )

        elif pod_type == "owned":
            pods = await self.get_user_pods(user_id, page, size)
            return (
                pods,
                "내가 개설한 파티 목록을 조회했습니다.",
                "Successfully retrieved my owned pods.",
            )

        elif pod_type == "following":
            if self._follow_use_case is None:
                raise InvalidPodTypeException(pod_type)
            pods = await self._follow_use_case.get_following_pods(
                user_id=user_id, page=page, size=size
            )
            return (
                pods,
                "팔로우하는 사용자의 파티 목록을 조회했습니다.",
                "Successfully retrieved following users' pods.",
            )

        else:
            raise InvalidPodTypeException(pod_type)

    # MARK: - 파티 검색 (검증 포함)
    async def search_pods_with_validation(
        self,
        user_id: int | None,
        title: str | None = None,
        main_category: str | None = None,
        sub_category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        location: list[str | None] | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDto]:
        """파티 검색 (날짜 검증 포함)"""
        # 날짜 검증
        if start_date and end_date and start_date > end_date:
            raise InvalidDateException("시작 날짜가 종료 날짜보다 늦습니다.")

        return await self.search_pods(
            user_id=user_id,
            title=title,
            main_category=main_category,
            sub_category=sub_category,
            start_date=start_date,
            end_date=end_date,
            location=location,
            page=page,
            size=size,
        )

    # MARK: - 사용자 파티 조회 (검증 포함)
    async def get_user_pods_with_validation(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """사용자가 개설한 파티 목록 조회 (사용자 존재 검증 포함)"""
        # 사용자 존재 확인
        user = await self._user_repo.get_by_id(user_id)
        if not user or user.is_del:
            raise UserNotFoundException(user_id)

        return await self.get_user_pods(user_id, page, size)
