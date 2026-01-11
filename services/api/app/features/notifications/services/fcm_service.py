"""
FCM 알림 서비스

Firebase Cloud Messaging을 통한 알림 전송 비즈니스 로직을 담당합니다.
순수 FCM 인프라는 app.core.fcm 모듈을 사용합니다.
"""

import logging
from datetime import datetime, timezone
from typing import Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.fcm import FCMClient, get_fcm_client
from app.features.notifications.repositories.notification_repository import (
    NotificationRepository,
)
from app.features.notifications.schemas import (
    FollowNotiSubType,
    PodNotiSubType,
    PodStatusNotiSubType,
    RecommendNotiSubType,
    ReviewNotiSubType,
    get_notification_category,
    get_notification_main_type,
)
from app.features.users.repositories import UserNotificationRepository

logger = logging.getLogger(__name__)


class FCMService:
    """Firebase Cloud Messaging 서비스"""

    def __init__(self, fcm_client: FCMClient | None = None):
        """FCM 서비스 초기화"""
        self._fcm_client = fcm_client or get_fcm_client()

    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: dict | None = None,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
        related_pod_id: int | None = None,
    ) -> bool:
        """
        FCM 푸시 알림 전송 및 DB 저장

        Args:
            token: FCM 토큰
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터 (선택사항)
            db: DB 세션 (알림 저장용, 선택사항)
            user_id: 사용자 ID (알림 받는 사람, 선택사항)
            related_user_id: 관련 유저 ID (알림 발생시킨 사람)
            related_pod_id: 관련 파티 ID (Optional)

        Returns:
            성공 여부
        """
        # 사용자 알림 설정 확인
        if db and user_id:
            settings_crud = UserNotificationRepository(db)
            category = (
                get_notification_category(data.get("type", "UNKNOWN"))
                if data
                else "POD"
            )
            should_send = await settings_crud.should_send_notification(
                user_id, category
            )

            if not should_send:
                logger.info(
                    f"사용자 {user_id}의 알림 설정에 의해 전송 취소됨 (카테고리: {category})"
                )
                return True  # 설정에 의해 전송하지 않았지만 성공으로 처리

            # 개인 대 개인 팔로우 알림 설정 확인 (FOLLOW 타입인 경우)
            if category == "COMMUNITY" and data and data.get("type") == "FOLLOW":
                from app.features.follow.repositories.follow_repository import (
                    FollowRepository,
                )

                follow_crud = FollowRepository(db)
                related_user_id_from_data = data.get("relatedId")

                if related_user_id_from_data:
                    try:
                        notification_enabled = (
                            await follow_crud.get_notification_status(
                                int(related_user_id_from_data), user_id
                            )
                        )

                        if notification_enabled is False:
                            logger.info(
                                f"개인 팔로우 알림 설정에 의해 전송 취소됨: "
                                f"follower_id={related_user_id_from_data}, following_id={user_id}"
                            )
                            return True
                    except (ValueError, TypeError):
                        pass

        # FCM 메시지 전송
        success, error_message = self._fcm_client.send_message(
            token=token,
            title=title,
            body=body,
            data=data,
        )

        if not success and error_message:
            # 토큰 관련 에러 처리
            if FCMClient.is_token_invalid_error(error_message):
                logger.warning(f"FCM 토큰이 유효하지 않습니다: {token[:20]}...")
                if db is not None:
                    await self._invalidate_token(token, db, user_id)
            elif FCMClient.is_apns_auth_error(error_message):
                logger.warning(f"APNS 인증 에러 발생 (토큰은 유효함): {token[:20]}...")
            return False

        # DB에 알림 저장
        if db and user_id:
            await self._save_notification_to_db(
                db=db,
                user_id=user_id,
                related_user_id=related_user_id,
                related_pod_id=related_pod_id,
                title=title,
                body=body,
                data=data,
            )

        return True

    async def _save_notification_to_db(
        self,
        db: AsyncSession,
        user_id: int,
        related_user_id: int | None,
        related_pod_id: int | None,
        title: str,
        body: str,
        data: dict | None,
    ) -> None:
        """알림을 DB에 저장"""
        try:
            if not data:
                logger.warning("FCM data가 None입니다. 알림 DB 저장을 건너뜁니다.")
                return

            notification_type = data.get("type", "UNKNOWN")
            notification_value = data.get("value", "UNKNOWN")

            # 채팅 메시지 알림은 DB에 저장하지 않음
            if notification_value == "CHAT_MESSAGE_RECEIVED":
                logger.info(
                    f"채팅 메시지 알림은 DB에 저장하지 않음 (FCM만 전송): user_id={user_id}"
                )
                return

            if notification_type == "UNKNOWN" or notification_value == "UNKNOWN":
                logger.warning(
                    f"FCM data에 필수 필드가 누락되었습니다: "
                    f"type={notification_type}, value={notification_value}"
                )
                return

            category = get_notification_category(notification_type)

            before_create = datetime.now(timezone.utc)
            logger.info(
                f"[알림 생성 전] user_id={user_id}, notification_value={notification_value}, "
                f"현재 시간(UTC): {before_create.isoformat()}"
            )

            notification_repo = NotificationRepository(db)
            notification = await notification_repo.create_notification(
                user_id=user_id,
                related_user_id=related_user_id,
                related_pod_id=related_pod_id,
                title=title,
                body=body,
                notification_type=notification_type,
                notification_value=notification_value,
                related_id=data.get("relatedId"),
                category=category,
            )

            created_at_value = getattr(notification, "created_at", None)
            created_at_str = (
                created_at_value.isoformat() if created_at_value is not None else "None"
            )
            logger.info(
                f"[알림 생성 후] notification_id={getattr(notification, 'id', 'Unknown')}, "
                f"user_id={user_id}, notification_value={notification_value}, "
                f"DB 저장 시간(UTC): {created_at_str}"
            )
        except Exception as db_error:
            logger.error(f"알림 DB 저장 실패: {db_error}")

    async def _invalidate_token(
        self, token: str, db: AsyncSession | None = None, user_id: int | None = None
    ):
        """유효하지 않은 FCM 토큰을 DB에서 제거"""
        try:
            if db is not None and user_id is not None:
                from app.features.users.repositories import UserRepository

                user_crud = UserRepository(db)
                await user_crud.update_fcm_token(user_id, None)
                logger.info(f"사용자 {user_id}의 무효한 FCM 토큰을 제거했습니다")
        except Exception as e:
            logger.error(f"FCM 토큰 무효화 실패: {e}")

    async def send_multicast_notification(
        self, tokens: list[str], title: str, body: str, data: dict | None = None
    ) -> dict:
        """
        여러 사용자에게 FCM 푸시 알림 전송

        Args:
            tokens: FCM 토큰 리스트
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터 (선택사항)

        Returns:
            {"success_count": int, "failure_count": int}
        """
        result = self._fcm_client.send_multicast_message(
            tokens=tokens,
            title=title,
            body=body,
            data=data,
        )
        return {
            "success_count": result["success_count"],
            "failure_count": result["failure_count"],
        }

    # ========== 메시지 포맷팅 ==========

    def _format_message(
        self,
        notification_type: Union[
            PodNotiSubType,
            PodStatusNotiSubType,
            RecommendNotiSubType,
            ReviewNotiSubType,
            FollowNotiSubType,
        ],
        **kwargs,
    ) -> tuple[str, dict]:
        """
        알림 메시지 포맷팅

        Args:
            notification_type: 알림 타입 (Enum)
            **kwargs: 메시지 템플릿에 사용될 변수들

        Returns:
            (formatted_message, data_dict)
        """
        message_template, placeholders, related_id_key = notification_type.value

        formatted_message = message_template
        for placeholder in placeholders:
            value = kwargs.get(placeholder, "")
            formatted_message = formatted_message.replace(f"[{placeholder}]", str(value))

        notification_type_class = notification_type.__class__.__name__
        main_type = get_notification_main_type(notification_type_class)

        data = {
            "type": main_type,
            "value": notification_type.name,
        }

        if related_id_key and related_id_key in kwargs:
            data["relatedId"] = str(kwargs[related_id_key])

        logger.info(f"FCM 데이터 생성: type={data['type']}, value={data['value']}")
        return formatted_message, data

    # ========== 파티 알림 ==========

    async def send_pod_join_request(
        self,
        token: str,
        nickname: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 참여 요청 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_JOIN_REQUEST, nickname=nickname, pod_id=pod_id
        )
        data["target_user_id"] = str(user_id) if user_id else ""

        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_request_approved(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
        related_pod_id: int | None = None,
    ) -> bool:
        """파티 참여 요청 승인 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_REQUEST_APPROVED, party_name=party_name, pod_id=pod_id
        )
        data["target_user_id"] = str(user_id) if user_id else ""

        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=related_pod_id or pod_id,
        )

    async def send_pod_request_rejected(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
        related_pod_id: int | None = None,
    ) -> bool:
        """파티 참여 요청 거절 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_REQUEST_REJECTED, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=related_pod_id or pod_id,
        )

    async def send_pod_new_member(
        self,
        token: str,
        nickname: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 새 멤버 참여 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_NEW_MEMBER,
            nickname=nickname,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_updated(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 정보 수정 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_UPDATED, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_confirmed(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 확정 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_CONFIRMED, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_canceled(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 취소 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_CANCELED, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_start_soon(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 시작 1시간 전 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_START_SOON, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_low_attendance(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 마감 임박 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_LOW_ATTENDANCE, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_canceled_soon(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 취소 임박 알림 전송"""
        body, data = self._format_message(
            PodNotiSubType.POD_CANCELED_SOON, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    # ========== 파티 상태 알림 ==========

    async def send_pod_likes_threshold(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 좋아요 10개 달성 알림 전송"""
        body, data = self._format_message(
            PodStatusNotiSubType.POD_LIKES_THRESHOLD,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_views_threshold(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 조회수 10회 달성 알림 전송"""
        body, data = self._format_message(
            PodStatusNotiSubType.POD_VIEWS_THRESHOLD,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_capacity_full(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 정원 가득 참 알림 전송 (파티장에게)"""
        body, data = self._format_message(
            PodStatusNotiSubType.POD_CAPACITY_FULL, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    # ========== 추천 알림 ==========

    async def send_saved_pod_deadline(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """좋아요한 파티 마감 임박 알림 전송"""
        body, data = self._format_message(
            RecommendNotiSubType.SAVED_POD_DEADLINE,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_saved_pod_spot_opened(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """좋아요한 파티에 자리 생김 알림 전송"""
        body, data = self._format_message(
            RecommendNotiSubType.SAVED_POD_SPOT_OPENED,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    # ========== 리뷰 알림 ==========

    async def send_review_created(
        self,
        token: str,
        nickname: str,
        party_name: str,
        review_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
        related_pod_id: int | None = None,
    ) -> bool:
        """리뷰 등록 알림 전송"""
        body, data = self._format_message(
            ReviewNotiSubType.REVIEW_CREATED,
            nickname=nickname,
            party_name=party_name,
            review_id=review_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=related_pod_id,
        )

    async def send_review_reminder_day(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
    ) -> bool:
        """리뷰 작성 유도 알림 (1일 후) 전송"""
        body, data = self._format_message(
            ReviewNotiSubType.REVIEW_REMINDER_DAY, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_pod_id=pod_id,
        )

    async def send_review_reminder_week(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
    ) -> bool:
        """리뷰 작성 리마인드 알림 (1주일 후) 전송"""
        body, data = self._format_message(
            ReviewNotiSubType.REVIEW_REMINDER_WEEK, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_pod_id=pod_id,
        )

    async def send_review_others_created(
        self,
        token: str,
        nickname: str,
        review_id: int,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """다른 참여자 리뷰 작성 알림 전송"""
        body, data = self._format_message(
            ReviewNotiSubType.REVIEW_OTHERS_CREATED,
            nickname=nickname,
            review_id=review_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    async def send_pod_completed(
        self,
        token: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """파티 완료 알림 전송"""
        body, data = self._format_message(
            PodStatusNotiSubType.POD_COMPLETED, party_name=party_name, pod_id=pod_id
        )

        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )

    # ========== 팔로우 알림 ==========

    async def send_followed_by_user(
        self,
        token: str,
        nickname: str,
        follow_user_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """팔로우 알림 전송"""
        body, data = self._format_message(
            FollowNotiSubType.FOLLOWED_BY_USER,
            nickname=nickname,
            follow_user_id=follow_user_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=None,
        )

    async def send_followed_user_created_pod(
        self,
        token: str,
        nickname: str,
        party_name: str,
        pod_id: int,
        db: AsyncSession | None = None,
        user_id: int | None = None,
        related_user_id: int | None = None,
    ) -> bool:
        """팔로우한 유저의 파티 생성 알림 전송"""
        body, data = self._format_message(
            FollowNotiSubType.FOLLOWED_USER_CREATED_POD,
            nickname=nickname,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token,
            title="PodPod",
            body=body,
            data=data,
            db=db,
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=pod_id,
        )
