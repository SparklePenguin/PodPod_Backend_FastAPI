import json
import math

from app.common.schemas import PageDto
from app.features.notifications.repositories.notification_repository import (
    NotificationRepository,
)
from app.features.notifications.schemas import (
    NotificationResponse,
    NotificationUnreadCountResponse,
    get_notification_main_type,
)
from app.features.pods.schemas import PodDto
from app.features.tendencies.repositories.tendency_repository import TendencyRepository
from app.features.users.schemas import UserDto
from sqlalchemy.ext.asyncio import AsyncSession


class NotificationService:
    """알림 Service"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._notification_repo = NotificationRepository(session)
        self._tendency_repo = TendencyRepository(session)

    # - MARK: 알림 목록 조회
    async def get_notifications(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        unread_only: bool = False,
        category: str | None = None,
    ) -> PageDto[NotificationResponse]:
        """사용자의 알림 목록 조회"""
        skip = (page - 1) * size

        # category를 대문자로 변환 (DB에는 대문자로 저장됨)
        category_upper = category.upper() if category else None

        # 알림 목록 조회
        notifications = await self._notification_repo.get_user_notifications(
            user_id=user_id,
            skip=skip,
            limit=size,
            unread_only=unread_only,
            category=category_upper,
        )

        # 전체 개수 조회
        total_count = await self._notification_repo.get_total_count(
            user_id=user_id, unread_only=unread_only, category=category_upper
        )

        # 총 페이지 수 계산
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        # DTO 변환
        notification_dtos = []
        for n in notifications:
            notification_dto = await self._convert_to_notification_response(n)
            notification_dtos.append(notification_dto)

        return PageDto[NotificationResponse](
            items=notification_dtos,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    # - MARK: 읽지 않은 알림 개수 조회
    async def get_unread_count(self, user_id: int) -> NotificationUnreadCountResponse:
        """읽지 않은 알림 개수 조회"""
        unread_count = await self._notification_repo.get_unread_count(user_id)
        return NotificationUnreadCountResponse(unread_count=unread_count)

    # - MARK: 알림 읽음 처리
    async def mark_as_read(
        self, notification_id: int, user_id: int
    ) -> NotificationResponse:
        """특정 알림을 읽음 처리"""
        notification = await self._notification_repo.mark_as_read(
            notification_id, user_id
        )

        if not notification:
            from app.features.notifications.exceptions import (
                NotificationNotFoundException,
            )

            raise NotificationNotFoundException(notification_id)

        return await self._convert_to_notification_response(notification)

    # - MARK: 모든 알림 읽음 처리
    async def mark_all_as_read(self, user_id: int) -> dict:
        """사용자의 모든 알림을 읽음 처리"""
        updated_count = await self._notification_repo.mark_all_as_read(user_id)
        return {"updatedCount": updated_count}

    # - MARK: 알림 삭제
    async def delete_notification(self, notification_id: int, user_id: int) -> dict:
        """특정 알림 삭제"""
        success = await self._notification_repo.delete_notification(
            notification_id, user_id
        )

        if not success:
            from app.features.notifications.exceptions import (
                NotificationNotFoundException,
            )

            raise NotificationNotFoundException(notification_id)

        return {"success": True}

    # - MARK: 읽은 알림 전체 삭제
    async def delete_all_read_notifications(self, user_id: int) -> dict:
        """읽은 알림 전체 삭제"""
        deleted_count = await self._notification_repo.delete_all_read_notifications(
            user_id
        )
        return {"deletedCount": deleted_count}

    # - MARK: 알림 모델을 DTO로 변환
    async def _convert_to_notification_response(
        self, notification
    ) -> NotificationResponse:
        """알림 모델을 NotificationResponse DTO로 변환"""
        # related_user DTO 생성
        related_user_dto = None
        if notification.related_user:
            # 사용자의 성향 정보 조회
            tendency_type = ""
            try:
                user_tendency = await self._tendency_repo.get_user_tendency_result(
                    notification.related_user.id
                )
                if user_tendency:
                    tendency_type_raw = user_tendency.tendency_type
                    tendency_type = (
                        str(tendency_type_raw)
                        if tendency_type_raw is not None
                        else ""
                    )
            except Exception:
                tendency_type = ""

            related_user_dto = UserDto(
                id=notification.related_user.id,
                nickname=notification.related_user.nickname,
                profile_image=notification.related_user.profile_image,
                intro=notification.related_user.intro or "",
                tendency_type=tendency_type,
                is_following=False,  # TODO: 필요시 조회
            )

        # related_pod DTO 생성
        related_pod_dto = None
        if notification.related_pod:
            from datetime import datetime, timezone

            # meeting_date와 meeting_time을 하나의 timestamp로 변환
            meeting_timestamp = 0
            if (
                notification.related_pod.meeting_date
                and notification.related_pod.meeting_time
            ):
                try:
                    dt = datetime.combine(
                        notification.related_pod.meeting_date,
                        notification.related_pod.meeting_time,
                        tzinfo=timezone.utc,
                    )
                    meeting_timestamp = int(dt.timestamp() * 1000)  # milliseconds
                except (ValueError, TypeError, AttributeError):
                    meeting_timestamp = 0

            # sub_categories를 문자열에서 리스트로 파싱
            sub_categories_list = []
            if notification.related_pod.sub_categories:
                try:
                    if isinstance(notification.related_pod.sub_categories, list):
                        sub_categories_list = notification.related_pod.sub_categories
                    else:
                        sub_categories_list = json.loads(
                            notification.related_pod.sub_categories
                        )
                except (json.JSONDecodeError, TypeError, AttributeError):
                    sub_categories_list = []

            related_pod_dto = PodDto(
                id=notification.related_pod.id,
                owner_id=notification.related_pod.owner_id,
                title=notification.related_pod.title,
                thumbnail_url=notification.related_pod.thumbnail_url
                or notification.related_pod.image_url
                or "",
                sub_categories=sub_categories_list,
                selected_artist_id=notification.related_pod.selected_artist_id or 0,
                capacity=notification.related_pod.capacity or 0,
                place=notification.related_pod.place or "",
                meeting_date=notification.related_pod.meeting_date,
                meeting_time=notification.related_pod.meeting_time,
                status=notification.related_pod.status,
                created_at=notification.related_pod.created_at,
                updated_at=notification.related_pod.updated_at,
            )

        # related_id를 int로 변환
        related_id_int: int | None = None
        if notification.related_id is not None:
            try:
                related_id_int = int(notification.related_id)
            except (ValueError, TypeError):
                related_id_int = None

        return NotificationResponse(
            id=notification.id,
            title=notification.title,
            body=notification.body,
            type=get_notification_main_type(notification.notification_type),
            value=notification.notification_value,
            related_id=related_id_int,
            category=notification.category,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
            related_user=related_user_dto,
            related_pod=related_pod_dto,
        )
