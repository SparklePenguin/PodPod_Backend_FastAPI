"""Pod Enrichment Service - Pod DTO 변환 및 추가 정보 설정"""

import logging
from collections import defaultdict
from datetime import date, datetime, time, timezone

from app.features.pods.models import Pod, PodImage, PodStatus
from app.features.pods.repositories.application_repository import ApplicationRepository
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.schemas import PodDetailDto, PodDto, PodImageDto
from app.features.pods.services.application_dto_service import ApplicationDtoService
from app.features.pods.services.pod_dto_service import PodDtoService
from app.features.pods.services.review_dto_service import ReviewDtoService
from app.features.users.repositories import UserRepository
from app.features.users.services.user_dto_service import UserDtoService


class PodEnrichmentService:
    """Pod DTO 변환 및 추가 정보를 설정하는 서비스"""

    def __init__(
        self,
        pod_repo: PodRepository,
        application_repo: ApplicationRepository,
        review_repo: PodReviewRepository,
        like_repo: PodLikeRepository,
        user_repo: UserRepository,
        application_dto_service: ApplicationDtoService,
        review_dto_service: ReviewDtoService,
    ):
        self._pod_repo = pod_repo
        self._application_repo = application_repo
        self._review_repo = review_repo
        self._like_repo = like_repo
        self._user_repo = user_repo
        self._application_dto_service = application_dto_service
        self._review_dto_service = review_dto_service
        self._user_dto_service = UserDtoService()

    async def enrich(self, pod: Pod, user_id: int | None = None) -> PodDetailDto:
        """Pod를 PodDetailDto로 변환하고 추가 정보를 설정"""
        pod_detail = pod.detail

        # 이미지 리스트 조회
        images_dto = []
        if pod.images:
            pod_images: list[PodImage] = list(pod.images)
            for img in sorted(pod_images, key=lambda x: x.display_order or 0):
                images_dto.append(PodImageDto.from_pod_image(img))

        # datetime 기본값 제공
        pod_created_at = pod.created_at
        if pod_created_at is None:
            pod_created_at = datetime.now(timezone.utc)

        pod_updated_at = pod.updated_at
        if pod_updated_at is None:
            pod_updated_at = datetime.now(timezone.utc)

        # sub_categories 파싱
        pod_sub_categories = PodDtoService.parse_sub_categories(pod.sub_categories)

        # 상태 처리
        pod_status = pod.status
        if pod_status is None:
            pod_status = PodStatus.RECRUITING
        elif isinstance(pod_status, str):
            try:
                pod_status = PodStatus(pod_status.upper())
            except ValueError:
                pod_status = PodStatus.RECRUITING

        pod_dto = PodDetailDto(
            id=pod.id or 0,
            owner_id=pod.owner_id or 0,
            title=pod.title or "",
            description=pod_detail.description if pod_detail else "",
            image_url=pod_detail.image_url if pod_detail else None,
            thumbnail_url=pod.thumbnail_url,
            sub_categories=pod_sub_categories,
            capacity=pod.capacity or 0,
            place=pod.place or "",
            address=pod_detail.address if pod_detail else "",
            sub_address=pod_detail.sub_address if pod_detail else None,
            x=pod_detail.x if pod_detail else None,
            y=pod_detail.y if pod_detail else None,
            meeting_date=pod.meeting_date if pod.meeting_date else date.today(),
            meeting_time=pod.meeting_time if pod.meeting_time else time.min,
            selected_artist_id=pod.selected_artist_id,
            status=pod_status,
            is_del=pod.is_del if pod.is_del else False,
            chat_room_id=pod.chat_room_id,
            images=images_dto,
            created_at=pod_created_at,
            updated_at=pod_updated_at,
            is_liked=False,
            applications=[],
            view_count=0,
            joined_users_count=0,
            like_count=0,
            joined_users=[],
        )

        # 통계 필드 설정
        if pod.id is not None:
            pod_dto.joined_users_count = await self._pod_repo.get_joined_users_count(
                pod.id
            )
            pod_dto.like_count = await self._like_repo.like_count(pod.id)
            pod_dto.view_count = await self._pod_repo.get_view_count(pod.id)

        # 참여 중인 유저 목록 조회
        if pod.id is None:
            return pod_dto
        pod_members = await self._application_repo.list_members(pod.id)

        joined_users = []

        # 파티장 추가
        if pod.owner_id is not None:
            owner = await self._user_repo.get_by_id(pod.owner_id)
            if owner:
                owner_tendency_type = await self._user_repo.get_user_tendency_type(
                    pod.owner_id
                )
                owner_dto = self._user_dto_service.create_user_dto(
                    owner, owner_tendency_type or ""
                )
                joined_users.append(owner_dto)

        # 멤버들 추가
        for member in pod_members:
            if member.user_id is None:
                continue
            user = await self._user_repo.get_by_id(member.user_id)
            if user:
                tendency_type = await self._user_repo.get_user_tendency_type(
                    member.user_id
                )
                user_dto = self._user_dto_service.create_user_dto(
                    user, tendency_type or ""
                )
                joined_users.append(user_dto)

        pod_dto.joined_users = joined_users

        # 사용자 정보가 있으면 개인화 필드 설정
        if user_id and pod.id is not None:
            pod_dto.is_liked = await self._pod_repo.is_liked_by_user(pod.id, user_id)
            existing_review = await self._review_repo.get_review_by_pod_and_user(
                pod.id, user_id
            )
            pod_dto.is_reviewed = existing_review is not None

        # 파티에 들어온 신청서 목록 조회
        if pod.id is None:
            return pod_dto
        applications = await self._application_repo.get_applications_by_pod_id(pod.id)

        application_dtos = []
        for app in applications:
            if app.user_id is None:
                continue
            application_dto = await self._application_dto_service.convert_to_list_dto(
                app, include_message=True
            )
            application_dtos.append(application_dto)

        pod_dto.applications = application_dtos

        # 후기 목록 조회 및 추가
        if pod.id is None:
            return pod_dto
        reviews = await self._review_repo.get_all_reviews_by_pod(pod.id)

        review_dtos = []
        for review in reviews:
            review_dto = await self._review_dto_service.convert_to_dto(review)
            review_dtos.append(review_dto)

        pod_dto.reviews = review_dtos
        return pod_dto

    async def convert_batch(
        self,
        pods: list[Pod],
        user_id: int | None = None,
        include_applications: bool = False,
        include_reviews: bool = False,
    ) -> list[PodDto]:
        """여러 Pod를 PodDto로 변환 (배치 로딩 방식, N+1 방지)

        Args:
            pods: Pod 모델 리스트
            user_id: 현재 사용자 ID
            include_applications: applications 포함 여부
            include_reviews: reviews 포함 여부
        """
        if not pods:
            return []

        logger = logging.getLogger(__name__)

        # pod_ids 수집
        pod_ids = [pod.id for pod in pods if pod.id is not None]

        # 배치 로딩 (필요한 경우만)
        applications = []
        reviews = []

        if include_applications:
            applications = await self._application_repo.get_applications_by_pod_ids(
                pod_ids
            )

        if include_reviews:
            reviews = await self._review_repo.get_reviews_by_pod_ids(pod_ids)

        # 메모리에서 매핑
        app_map = defaultdict(list)
        for app in applications:
            app_map[app.pod_id].append(app)

        review_map = defaultdict(list)
        for review in reviews:
            review_map[review.pod_id].append(review)

        # 순수 함수로 조립 (쿼리 없음)
        pod_dtos = []
        for pod in pods:
            try:
                pod_dto = PodDtoService.convert_to_dto(pod)
                pod_dtos.append(pod_dto)
            except Exception as e:
                logger.error(
                    f"파티 DTO 변환 실패 (pod_id={pod.id if pod else None}): {str(e)}",
                    exc_info=True,
                )
                continue

        return pod_dtos
