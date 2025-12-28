from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.features.follow.repositories.follow_repository import FollowCRUD
from app.features.follow.schemas import (
    FollowNotificationStatusResponse,
    FollowResponse,
    FollowStatsResponse,
    SimpleUserDto,
)
from app.features.follow.exceptions import (
    FollowFailedException,
    FollowInvalidException,
)
from app.features.pods.repositories.pod_repository import PodCRUD
from app.features.pods.schemas import PodDto
from app.features.users.repositories import UserRepository
from app.common.schemas import PageDto
from app.core.services.fcm_service import FCMService
from sqlalchemy import select
from app.features.users.models import User
import logging

logger = logging.getLogger(__name__)


class FollowService:
    """팔로우 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._follow_repo = FollowCRUD(db)
        self._pod_repo = PodCRUD(db)
        self._user_repo = UserRepository(db)
        from app.features.pods.repositories.review_repository import PodReviewCRUD

        self._review_repo = PodReviewCRUD(db)

    async def follow_user(self, follower_id: int, following_id: int) -> FollowResponse:
        """사용자 팔로우"""
        follow = await self._follow_repo.create_follow(follower_id, following_id)

        if not follow:
            raise FollowFailedException(follower_id, following_id)

        # 팔로우 알림 전송
        await self._send_follow_notification(follower_id, following_id)

        follower_id_value = getattr(follow, "follower_id", None)
        following_id_value = getattr(follow, "following_id", None)
        created_at_value = getattr(follow, "created_at", None)
        
        if follower_id_value is None or following_id_value is None:
            raise FollowInvalidException("팔로우 정보가 올바르지 않습니다.")
        
        if created_at_value is None:
            from datetime import datetime, timezone
            created_at_value = datetime.now(timezone.utc).replace(tzinfo=None)
        
        return FollowResponse(
            follower_id=follower_id_value,
            following_id=following_id_value,
            created_at=created_at_value,
        )

    async def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        """사용자 팔로우 취소"""
        return await self._follow_repo.delete_follow(follower_id, following_id)

    async def get_following_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[SimpleUserDto]:
        """팔로우하는 사용자 목록 조회"""
        following_data, total_count = await self._follow_repo.get_following_list(
            user_id, page, size
        )

        users = []
        for user, created_at, tendency_type in following_data:
            user_id_val = getattr(user, "id", None)
            if user_id_val is None or not isinstance(user_id_val, int):
                continue
            user_id = user_id_val
            user_nickname = getattr(user, "nickname", "") or ""
            user_profile_image = getattr(user, "profile_image", None) or ""
            user_intro = getattr(user, "intro", None) or ""
            tendency_type_str = tendency_type or "" if tendency_type is not None else ""
            
            if user_id is None:
                continue
                
            user_dto = SimpleUserDto(
                id=user_id,
                nickname=user_nickname,
                profile_image=user_profile_image,
                intro=user_intro,
                tendency_type=tendency_type_str,
                is_following=True,  # 팔로우하는 사용자 목록이므로 항상 True
            )
            users.append(user_dto)

        has_next = (page * size) < total_count

        # PageDto 생성
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto(
            items=users,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def get_followers_list(
        self,
        user_id: int,
        current_user_id: Optional[int] = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[SimpleUserDto]:
        """팔로워 목록 조회"""
        followers_data, total_count = await self._follow_repo.get_followers_list(
            user_id, page, size
        )

        users = []
        for user, created_at, tendency_type in followers_data:
            user_id_val = getattr(user, "id", None)
            if user_id_val is None or not isinstance(user_id_val, int):
                continue
            user_id = user_id_val
                
            # 현재 사용자가 해당 팔로워를 팔로우하고 있는지 확인
            is_following = False
            if current_user_id:
                is_following = await self._follow_repo.check_follow_exists(
                    current_user_id, user_id
                )

            user_nickname = getattr(user, "nickname", "") or ""
            user_profile_image = getattr(user, "profile_image", None) or ""
            user_intro = getattr(user, "intro", None) or ""
            tendency_type_str = tendency_type or "" if tendency_type is not None else ""

            user_dto = SimpleUserDto(
                id=user_id,
                nickname=user_nickname,
                profile_image=user_profile_image,
                intro=user_intro,
                tendency_type=tendency_type_str,
                is_following=is_following,
            )
            users.append(user_dto)

        # PageDto 생성
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto(
            items=users,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def get_follow_stats(
        self, user_id: int, current_user_id: Optional[int] = None
    ) -> FollowStatsResponse:
        """팔로우 통계 조회"""
        stats = await self._follow_repo.get_follow_stats(user_id, current_user_id)

        return FollowStatsResponse(
            following_count=stats["following_count"],
            followers_count=stats["followers_count"],
            is_following=stats["is_following"],
        )

    async def get_following_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """팔로우하는 사용자가 만든 파티 목록 조회"""
        pods, total_count = await self._follow_repo.get_following_pods(user_id, page, size)

        pod_dtos = []
        for pod in pods:
            pod_id = getattr(pod, "id", None)
            if pod_id is None:
                continue
                
            # 각 파티의 참여자 수와 좋아요 수 계산
            joined_users_count = await self._pod_repo.get_joined_users_count(pod_id)
            like_count = await self._pod_repo.get_like_count(pod_id)
            view_count = await self._pod_repo.get_view_count(pod_id)

            # 사용자가 좋아요했는지 확인
            is_liked = await self._pod_repo.is_liked_by_user(pod_id, user_id)

            # meeting_date와 meeting_time을 timestamp로 변환 (UTC로 저장된 값이므로 UTC로 해석)
            def _convert_to_timestamp(meeting_date, meeting_time):
                """date와 time 객체를 UTC로 해석하여 timestamp로 변환"""
                if meeting_date is None:
                    return None
                from datetime import datetime, time as time_module, timezone

                if meeting_time is None:
                    dt = datetime.combine(
                        meeting_date, time_module.min, tzinfo=timezone.utc
                    )
                else:
                    dt = datetime.combine(
                        meeting_date, meeting_time, tzinfo=timezone.utc
                    )
                return int(dt.timestamp() * 1000)  # milliseconds

            # PodDto를 수동으로 생성하여 MissingGreenlet 오류 방지
            # 후기 목록 조회
            reviews = await self._review_repo.get_all_reviews_by_pod(pod_id)
            from app.features.pods.services.review_service import PodReviewService

            review_service = PodReviewService(self._db)
            review_dtos = []
            for review in reviews:
                review_dto = await review_service._convert_to_dto(review)
                review_dtos.append(review_dto)

            # Pod 속성 안전하게 추출
            pod_owner_id = getattr(pod, "owner_id", None)
            pod_title = getattr(pod, "title", "") or ""
            pod_description = getattr(pod, "description", "") or ""
            pod_image_url = getattr(pod, "image_url", None)
            pod_thumbnail_url = getattr(pod, "thumbnail_url", None)
            pod_sub_categories = getattr(pod, "sub_categories", None)
            pod_capacity = getattr(pod, "capacity", 0) or 0
            pod_place = getattr(pod, "place", "") or ""
            pod_address = getattr(pod, "address", "") or ""
            pod_sub_address = getattr(pod, "sub_address", None)
            pod_x = getattr(pod, "x", None)
            pod_y = getattr(pod, "y", None)
            pod_meeting_date = getattr(pod, "meeting_date", None)
            pod_meeting_time = getattr(pod, "meeting_time", None)
            pod_selected_artist_id = getattr(pod, "selected_artist_id", None)
            pod_status = getattr(pod, "status", None)
            pod_chat_channel_url = getattr(pod, "chat_channel_url", None)
            pod_created_at = getattr(pod, "created_at", None)
            pod_updated_at = getattr(pod, "updated_at", None)
            
            # sub_categories가 문자열인 경우 파싱 필요할 수 있음
            if pod_sub_categories is None:
                pod_sub_categories = []
            elif isinstance(pod_sub_categories, str):
                import json
                try:
                    pod_sub_categories = json.loads(pod_sub_categories) if pod_sub_categories else []
                except (ValueError, TypeError, json.JSONDecodeError):
                    pod_sub_categories = []
            
            from datetime import datetime, timezone
            if pod_created_at is None:
                pod_created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            if pod_updated_at is None:
                pod_updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            # 타입 체크 및 변환
            from app.features.pods.models.pod.pod_status import PodStatus
            
            pod_owner_id_int = pod_owner_id if isinstance(pod_owner_id, int) else None
            if pod_owner_id_int is None:
                continue  # owner_id가 없으면 건너뛰기
            
            pod_status_enum = None
            if pod_status is not None:
                if isinstance(pod_status, PodStatus):
                    pod_status_enum = pod_status
                elif isinstance(pod_status, str):
                    try:
                        pod_status_enum = PodStatus(pod_status.upper())
                    except ValueError:
                        pod_status_enum = PodStatus.RECRUITING  # 기본값
                else:
                    pod_status_enum = PodStatus.RECRUITING  # 기본값
            else:
                pod_status_enum = PodStatus.RECRUITING  # 기본값
            
            pod_dto = PodDto(
                id=pod_id,
                owner_id=pod_owner_id_int,
                title=pod_title,
                description=pod_description,
                image_url=pod_image_url,
                thumbnail_url=pod_thumbnail_url,
                sub_categories=pod_sub_categories,
                capacity=pod_capacity,
                place=pod_place,
                address=pod_address,
                sub_address=pod_sub_address,
                x=pod_x,  # x 좌표 추가
                y=pod_y,  # y 좌표 추가
                meeting_date=_convert_to_timestamp(pod_meeting_date, pod_meeting_time),
                selected_artist_id=pod_selected_artist_id,
                status=pod_status_enum,
                chat_channel_url=pod_chat_channel_url,
                created_at=pod_created_at,
                updated_at=pod_updated_at,
                # 실제 값 설정
                is_liked=is_liked,
                my_application=None,
                applications=[],
                view_count=view_count,
                joined_users_count=joined_users_count,
                like_count=like_count,
                joined_users=[],  # 팔로우 파티 목록에서는 빈 배열로 설정
                reviews=review_dtos,  # 후기 목록
            )

            pod_dtos.append(pod_dto)

        # PageDto 생성
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto(
            items=pod_dtos,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def get_recommended_users(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[SimpleUserDto]:
        """추천 유저 목록 조회 (현재는 랜덤 유저 반환)"""
        recommended_users = await self._follow_repo.get_recommended_users(user_id, page, size)

        users = []
        for user, tendency_type in recommended_users:
            user_id_val = getattr(user, "id", None)
            if user_id_val is None or not isinstance(user_id_val, int):
                continue
            user_id = user_id_val
                
            user_nickname = getattr(user, "nickname", "") or ""
            user_profile_image = getattr(user, "profile_image", None) or ""
            user_intro = getattr(user, "intro", None) or ""
            tendency_type_str = tendency_type or "" if tendency_type is not None else ""

            user_dto = SimpleUserDto(
                id=user_id,
                nickname=user_nickname,
                profile_image=user_profile_image,
                intro=user_intro,
                tendency_type=tendency_type_str,
                is_following=False,  # 추천 유저는 팔로우하지 않은 유저만 추천
            )
            users.append(user_dto)

        # 추천 유저는 총 개수를 정확히 알 수 없으므로 간단하게 처리
        total_count = len(users)
        total_pages = 1 if total_count > 0 else 0
        has_next = False  # 추천 유저는 한 페이지만 제공
        has_prev = False

        return PageDto(
            items=users,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def get_notification_status(
        self, follower_id: int, following_id: int
    ) -> Optional[FollowNotificationStatusResponse]:
        """특정 팔로우 관계의 알림 설정 상태 조회"""
        notification_enabled = await self._follow_repo.get_notification_status(
            follower_id, following_id
        )

        if notification_enabled is None:
            return None

        return FollowNotificationStatusResponse(
            following_id=following_id,
            notification_enabled=notification_enabled,
        )

    async def update_notification_status(
        self, follower_id: int, following_id: int, notification_enabled: bool
    ) -> Optional[FollowNotificationStatusResponse]:
        """특정 팔로우 관계의 알림 설정 상태 변경"""
        success = await self._follow_repo.update_notification_status(
            follower_id, following_id, notification_enabled
        )

        if not success:
            return None

        return FollowNotificationStatusResponse(
            following_id=following_id,
            notification_enabled=notification_enabled,
        )

    # - MARK: 팔로우 알림 전송
    async def _send_follow_notification(
        self, follower_id: int, following_id: int
    ) -> None:
        """팔로우 알림 전송"""
        try:
            # 팔로우한 사용자 정보 조회
            follower_result = await self._db.execute(
                select(User).where(User.id == follower_id)
            )
            follower = follower_result.scalar_one_or_none()

            # 팔로우받은 사용자 정보 조회
            following_result = await self._db.execute(
                select(User).where(User.id == following_id)
            )
            following = following_result.scalar_one_or_none()

            if not follower or not following:
                logger.warning(
                    f"사용자 정보를 찾을 수 없음: follower_id={follower_id}, following_id={following_id}"
                )
                return

            # 팔로우받은 사용자의 FCM 토큰 확인
            following_fcm_token = getattr(following, "fcm_token", None)
            follower_nickname = getattr(follower, "nickname", "") or ""
            
            if following_fcm_token:
                # FCM 서비스 초기화
                fcm_service = FCMService()

                # 팔로우 알림 전송
                await fcm_service.send_followed_by_user(
                    token=following_fcm_token,
                    nickname=follower_nickname,
                    follow_user_id=follower_id,
                    db=self.db,
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
            pod_owner_result = await self._db.execute(
                select(User).where(User.id == pod_owner_id)
            )
            pod_owner = pod_owner_result.scalar_one_or_none()
            if not pod_owner:
                logger.warning(
                    f"파티 생성자 정보를 찾을 수 없음: pod_owner_id={pod_owner_id}"
                )
                return

            # 파티 생성자의 팔로워 목록 조회
            followers_data, _ = await self._follow_repo.get_followers_list(
                pod_owner_id, page=1, size=1000
            )  # 모든 팔로워 조회

            if not followers_data:
                logger.info(f"파티 생성자의 팔로워가 없음: pod_owner_id={pod_owner_id}")
                return

            # FCM 서비스 초기화
            fcm_service = FCMService()

            # 각 팔로워에게 알림 전송
            pod_owner_nickname = getattr(pod_owner, "nickname", "") or ""
            pod_title = getattr(pod, "title", "") or ""
            
            for follower_user, _, _ in followers_data:
                try:
                    follower_user_id = getattr(follower_user, "id", None)
                    follower_fcm_token = getattr(follower_user, "fcm_token", None)
                    
                    if follower_user_id is None:
                        continue
                        
                    if follower_fcm_token:
                        await fcm_service.send_followed_user_created_pod(
                            token=follower_fcm_token,
                            nickname=pod_owner_nickname,  # 파티장의 닉네임
                            party_name=pod_title,
                            pod_id=pod_id,
                            db=self.db,
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
                    follower_user_id = getattr(follower_user, "id", None) if follower_user else None
                    logger.error(
                        f"팔로워 알림 전송 실패: follower_id={follower_user_id}, error={e}"
                    )

        except Exception as e:
            logger.error(
                f"팔로우한 유저 파티 생성 알림 처리 중 오류: pod_owner_id={pod_owner_id}, pod_id={pod_id}, error={e}"
            )
