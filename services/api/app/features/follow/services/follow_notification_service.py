import logging

from app.features.notifications.services.fcm_service import FCMService
from app.features.follow.repositories.follow_list_repository import (
    FollowListRepository,
)
from app.features.follow.repositories.follow_notification_repository import (
    FollowNotificationRepository,
)
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.follow.schemas import FollowNotificationStatusDto
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FollowNotificationService:
    """팔로우 알림 서비스"""

    def __init__(
        self,
        session: AsyncSession,
        follow_noti_repo: FollowNotificationRepository,
        follow_repo: FollowRepository,
        follow_list_repo: FollowListRepository,
        pod_repo: PodRepository,
        user_repo: UserRepository,
        fcm_service: FCMService,
    ):
        self._session = session
        self._follow_noti_repo = follow_noti_repo
        self._follow_repo = follow_repo
        self._follow_list_repo = follow_list_repo
        self._pod_repo = pod_repo
        self._user_repo = user_repo
        self._fcm_service = fcm_service

    # - MARK: 특정 팔로우 관계의 알림 설정 상태 조회
    async def get_notification_status(
        self, follower_id: int, following_id: int
    ) -> FollowNotificationStatusDto | None:
        """특정 팔로우 관계의 알림 설정 상태 조회"""
        notification_enabled = await self._follow_noti_repo.get_notification_status(
            follower_id, following_id
        )

        if notification_enabled is None:
            return None

        return FollowNotificationStatusDto(
            following_id=following_id, notification_enabled=notification_enabled
        )

    # - MARK: 특정 팔로우 관계의 알림 설정 상태 변경
    async def update_notification_status(
        self, follower_id: int, following_id: int, notification_enabled: bool
    ) -> FollowNotificationStatusDto | None:
        """특정 팔로우 관계의 알림 설정 상태 변경"""
        success = await self._follow_noti_repo.update_notification_status(
            follower_id, following_id, notification_enabled
        )

        if not success:
            return None

        return FollowNotificationStatusDto(
            following_id=following_id, notification_enabled=notification_enabled
        )

    # - MARK: 팔로우 알림 전송
    async def send_follow_notification(
        self, follower_id: int, following_id: int
    ) -> None:
        """팔로우 알림 전송"""
        try:
            # 팔로우한 사용자 정보 조회
            follower = await self._user_repo.get_by_id(follower_id)

            # 팔로우받은 사용자 정보 조회
            following = await self._user_repo.get_by_id(following_id)

            if not follower or not following:
                logger.warning(
                    f"사용자 정보를 찾을 수 없음: follower_id={follower_id}, following_id={following_id}"
                )
                return

            # 팔로우받은 사용자의 FCM 토큰 확인
            following_fcm_token = (
                following.detail.fcm_token if following.detail else None
            )
            follower_nickname = follower.nickname or ""

            if following_fcm_token:
                # 팔로우 알림 전송
                await self._fcm_service.send_followed_by_user(
                    token=following_fcm_token,
                    nickname=follower_nickname,
                    follow_user_id=follower_id,
                    db=self._session,
                    user_id=following_id,
                    related_user_id=follower_id,
                )
                logger.info(
                    f"팔로우 알림 전송 성공: follower_id={follower_id}, following_id={following_id}"
                )
            else:
                logger.warning(
                    f"팔로우받은 사용자의 FCM 토큰이 없음: following_id={following_id}"
                )

        except Exception as e:
            logger.error(
                f"팔로우 알림 전송 실패: follower_id={follower_id}, following_id={following_id}, error={e}"
            )

    # - MARK: 팔로우한 유저의 파티 생성 알림
    async def send_followed_user_pod_created_notification(
        self, pod_owner_id: int, pod_id: int
    ) -> None:
        """팔로우한 유저가 파티 생성 시 팔로워들에게 알림 전송"""
        try:
            # 파티 정보 조회
            pod = await self._pod_repo.get_pod_by_id(pod_id)
            if not pod:
                logger.warning(f"파티 정보를 찾을 수 없음: pod_id={pod_id}")
                return

            # 파티 생성자 정보 조회
            pod_owner = await self._user_repo.get_by_id(pod_owner_id)
            if not pod_owner:
                logger.warning(
                    f"파티 생성자 정보를 찾을 수 없음: pod_owner_id={pod_owner_id}"
                )
                return

            # 파티 생성자의 팔로워 목록 조회
            followers_data, _ = await self._follow_list_repo.get_followers_list(
                pod_owner_id, page=1, size=1000
            )  # 모든 팔로워 조회

            if not followers_data:
                logger.info(f"파티 생성자의 팔로워가 없음: pod_owner_id={pod_owner_id}")
                return

            # 각 팔로워에게 알림 전송
            pod_owner_nickname = pod_owner.nickname or ""
            pod_title = pod.title or ""

            for follower_user, _, _ in followers_data:
                try:
                    if follower_user.id is None:
                        continue
                    follower_user_id = follower_user.id
                    follower_fcm_token = (
                        follower_user.detail.fcm_token if follower_user.detail else None
                    )

                    if follower_fcm_token:
                        await self._fcm_service.send_followed_user_created_pod(
                            token=follower_fcm_token,
                            nickname=pod_owner_nickname,  # 파티장의 닉네임
                            party_name=pod_title,
                            pod_id=pod_id,
                            db=self._session,
                            user_id=follower_user_id,
                            related_user_id=pod_owner_id,
                        )
                        logger.info(
                            f"팔로우한 유저 파티 생성 알림 전송 성공: follower_id={follower_user_id}, pod_id={pod_id}"
                        )
                    else:
                        logger.warning(
                            f"팔로워의 FCM 토큰이 없음: follower_id={follower_user_id}"
                        )
                except Exception as e:
                    follower_user_id = follower_user.id if follower_user else None
                    logger.error(
                        f"팔로워 알림 전송 실패: follower_id={follower_user_id}, error={e}"
                    )

        except Exception as e:
            logger.error(
                f"팔로우한 유저 파티 생성 알림 처리 중 오류: pod_owner_id={pod_owner_id}, pod_id={pod_id}, error={e}"
            )
