"""Follow Use Case - 비즈니스 로직 처리"""

from app.common.schemas import PageDto
from app.core.services.fcm_service import FCMService
from app.features.follow.exceptions import (
    FollowFailedException,
    FollowInvalidException,
    FollowNotFoundException,
)
from app.features.follow.repositories.follow_list_repository import FollowListRepository
from app.features.follow.repositories.follow_notification_repository import (
    FollowNotificationRepository,
)
from app.features.follow.repositories.follow_pod_repository import FollowPodRepository
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.follow.repositories.follow_stats_repository import (
    FollowStatsRepository,
)
from app.features.follow.schemas import (
    FollowInfoDto,
    FollowNotificationStatusDto,
    FollowStatsDto,
)
from app.features.follow.services.follow_dto_service import FollowDtoService
from app.features.follow.services.follow_notification_service import (
    FollowNotificationService,
)
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.schemas import PodDetailDto
from app.features.users.schemas import UserDto
from sqlalchemy.ext.asyncio import AsyncSession


class FollowUseCase:
    """팔로우 Use Case - 비즈니스 로직 통합"""

    def __init__(self, session: AsyncSession, fcm_service: FCMService | None = None):
        self._session = session
        self._follow_repo = FollowRepository(session)
        self._follow_list_repo = FollowListRepository(session)
        self._follow_stats_repo = FollowStatsRepository(session)
        self._follow_notification_repo = FollowNotificationRepository(session)
        self._follow_pod_repo = FollowPodRepository(session)
        self._pod_repo = PodRepository(session)
        self._like_repo = PodLikeRepository(session)
        self._review_repo = PodReviewRepository(session)
        self._follow_notification_service = FollowNotificationService(
            session, fcm_service
        )

    # - MARK: 사용자 팔로우
    async def follow_user(self, follower_id: int, following_id: int) -> FollowInfoDto:
        """사용자 팔로우"""
        follow = await self._follow_repo.create_follow(follower_id, following_id)
        await self._session.commit()

        if not follow:
            raise FollowFailedException(follower_id, following_id)

        if follow.follower_id is None or follow.following_id is None:
            raise FollowInvalidException("팔로우 정보가 올바르지 않습니다.")

        follow_info = FollowInfoDto.model_validate(follow)

        # 팔로우 알림 전송
        await self._follow_notification_service.send_follow_notification(
            follower_id, following_id
        )

        return follow_info

    # - MARK: 사용자 팔로우 취소
    async def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        """사용자 팔로우 취소"""
        success = await self._follow_repo.delete_follow(follower_id, following_id)
        await self._session.commit()

        if not success:
            raise FollowNotFoundException(follower_id, following_id)
        return success

    # - MARK: 팔로우하는 사용자 목록 조회
    async def get_following_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserDto]:
        """팔로우하는 사용자 목록 조회"""
        following_data, total_count = await self._follow_list_repo.get_following_list(
            user_id, page, size
        )

        users = []
        for user, _, tendency_type in following_data:
            try:
                user_dto = FollowDtoService.create_user_dto(
                    user, tendency_type=tendency_type, is_following=True
                )
                users.append(user_dto)
            except ValueError:
                continue

        return FollowDtoService.create_page_dto(users, page, size, total_count)

    # - MARK: 팔로워 목록 조회
    async def get_followers_list(
        self,
        user_id: int,
        current_user_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[UserDto]:
        """팔로워 목록 조회"""
        followers_data, total_count = await self._follow_list_repo.get_followers_list(
            user_id, page, size
        )

        # N+1 문제 해결: 현재 사용자가 팔로우하는 사용자 ID 목록을 한 번에 조회
        following_user_ids = await self._get_following_user_ids(
            current_user_id, followers_data
        )

        users = []
        for user, _, tendency_type in followers_data:
            try:
                follower_user_id = user.id
                is_following = (
                    follower_user_id in following_user_ids
                    if current_user_id and follower_user_id
                    else False
                )
                user_dto = FollowDtoService.create_user_dto(
                    user, tendency_type=tendency_type, is_following=is_following
                )
                users.append(user_dto)
            except ValueError:
                continue

        return FollowDtoService.create_page_dto(users, page, size, total_count)

    # - MARK: 현재 사용자가 팔로우하는 사용자 ID 목록 조회
    async def _get_following_user_ids(
        self, current_user_id: int | None, users_data: list
    ) -> set[int]:
        """현재 사용자가 팔로우하는 사용자 ID 목록을 한 번에 조회"""
        if not current_user_id:
            return set()

        user_ids = [user.id for user, _, _ in users_data if user.id]
        if not user_ids:
            return set()

        following_ids = await self._follow_list_repo.get_following_ids_by_user_ids(
            current_user_id, user_ids
        )
        return set(following_ids)

    # - MARK: 팔로우 통계 조회
    async def get_follow_stats(
        self, user_id: int, current_user_id: int | None = None
    ) -> FollowStatsDto:
        """팔로우 통계 조회"""
        stats = await self._follow_stats_repo.get_follow_stats(user_id, current_user_id)

        return FollowStatsDto(**stats)

    # - MARK: 추천 유저 목록 조회
    async def get_recommended_users(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserDto]:
        """추천 유저 목록 조회 (현재는 랜덤 유저 반환)"""
        recommended_users = await self._follow_list_repo.get_recommended_users(
            user_id, page, size
        )

        users = []
        for user, tendency_type in recommended_users:
            try:
                user_dto = FollowDtoService.create_user_dto(
                    user, tendency_type=tendency_type, is_following=False
                )
                users.append(user_dto)
            except ValueError:
                continue

        total_count = len(users)
        return FollowDtoService.create_page_dto(users, page, size, total_count)

    # - MARK: 특정 팔로우 관계의 알림 설정 상태 조회
    async def get_notification_status(
        self, follower_id: int, following_id: int
    ) -> FollowNotificationStatusDto | None:
        """특정 팔로우 관계의 알림 설정 상태 조회"""
        follow = await self._follow_repo.get_follow(follower_id, following_id)
        if not follow:
            return None

        return FollowNotificationStatusDto.model_validate(follow)

    # - MARK: 특정 팔로우 관계의 알림 설정 상태 변경
    async def update_notification_status(
        self, follower_id: int, following_id: int, notification_enabled: bool
    ) -> FollowNotificationStatusDto | None:
        """특정 팔로우 관계의 알림 설정 상태 변경"""
        follow = await self._follow_notification_repo.update_notification_status(
            follower_id, following_id, notification_enabled
        )
        await self._session.commit()

        if not follow:
            return None

        return FollowNotificationStatusDto.model_validate(follow)

    # - MARK: 팔로우한 유저의 파티 생성 알림
    async def send_followed_user_pod_created_notification(
        self, pod_owner_id: int, pod_id: int
    ) -> None:
        """팔로우한 유저가 파티 생성 시 팔로워들에게 알림 전송"""
        await self._follow_notification_service.send_followed_user_pod_created_notification(
            pod_owner_id, pod_id
        )

    # - MARK: 팔로우하는 사용자가 만든 파티 목록 조회
    async def get_following_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDetailDto]:
        """팔로우하는 사용자가 만든 파티 목록 조회"""
        from app.features.pods.services.pod_dto_service import PodDtoService
        from app.features.pods.services.review_dto_service import ReviewDtoService

        pods, total_count = await self._follow_pod_repo.get_following_pods(
            user_id, page, size
        )

        review_dto_service = ReviewDtoService(self._session, self._user_repo)

        pod_dtos = []
        for pod in pods:
            if pod.id is None or pod.owner_id is None:
                continue
            pod_id = pod.id

            # 기본 PodDetailDto 생성
            pod_dto = PodDtoService.convert_to_detail_dto(pod)

            # 통계 필드 설정
            pod_dto.joined_users_count = await self._pod_repo.get_joined_users_count(
                pod_id
            )
            pod_dto.like_count = await self._like_repo.like_count(pod_id)
            pod_dto.view_count = await self._pod_repo.get_view_count(pod_id)

            # 사용자가 좋아요했는지 확인
            pod_dto.is_liked = await self._pod_repo.is_liked_by_user(pod_id, user_id)

            # 후기 목록 조회
            reviews = await self._review_repo.get_all_reviews_by_pod(pod_id)
            review_dtos = []
            for review in reviews:
                review_dto = await review_dto_service.convert_to_dto(review)
                review_dtos.append(review_dto)
            pod_dto.reviews = review_dtos

            pod_dtos.append(pod_dto)

        return FollowDtoService.create_page_dto(pod_dtos, page, size, total_count)
