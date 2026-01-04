import logging
from typing import List, Union

import firebase_admin
from app.core.config import settings
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
from firebase_admin import credentials, messaging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FCMService:
    """Firebase Cloud Messaging 서비스"""

    _initialized = False

    def __init__(self):
        """FCM 서비스 초기화"""
        if not FCMService._initialized:
            try:
                # Firebase 서비스 계정 키 확인
                if not hasattr(settings, "FIREBASE_SERVICE_ACCOUNT_KEY"):
                    raise ValueError(
                        "Firebase 서비스 계정 키가 설정되지 않았습니다. "
                        "FIREBASE_SERVICE_ACCOUNT_KEY 환경변수를 설정해주세요."
                    )

                # JSON 문자열을 dict로 변환
                import json

                firebase_key = settings.FIREBASE_SERVICE_ACCOUNT_KEY
                if not firebase_key:
                    raise ValueError(
                        "FIREBASE_SERVICE_ACCOUNT_KEY 환경변수가 비어있습니다."
                    )
                service_account_info = json.loads(firebase_key)

                # Firebase Admin SDK 초기화
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)

                FCMService._initialized = True
                logger.info("Firebase Admin SDK 초기화 완료")

            except ValueError as e:
                logger.warning(f"Firebase 설정 오류: {e}")
                raise
            except Exception as e:
                logger.error(f"Firebase 초기화 실패: {e}")
                raise

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
        try:
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
                    related_user_id = data.get("relatedId")

                    if related_user_id:
                        try:
                            # 팔로우 관계의 개인 알림 설정 확인
                            notification_enabled = (
                                await follow_crud.get_notification_status(
                                    int(related_user_id), user_id
                                )
                            )

                            if notification_enabled is False:
                                logger.info(
                                    f"개인 팔로우 알림 설정에 의해 전송 취소됨: follower_id={related_user_id}, following_id={user_id}"
                                )
                                return (
                                    True  # 설정에 의해 전송하지 않았지만 성공으로 처리
                                )
                        except (ValueError, TypeError):
                            # relatedId가 숫자가 아닌 경우 무시
                            pass

            # 메시지 생성
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
            )

            # 메시지 전송
            response = messaging.send(message)
            logger.info(f"FCM 알림 전송 성공: {response}")

            # DB에 알림 저장 (db와 user_id가 제공된 경우에만)
            # 단, 채팅 메시지 알림(CHAT_MESSAGE_RECEIVED)은 DB에 저장하지 않음
            if db and user_id:
                try:
                    if not data:
                        logger.warning(
                            "FCM data가 None입니다. 알림 DB 저장을 건너뜁니다."
                        )
                        return True

                    notification_type = data.get("type", "UNKNOWN")
                    notification_value = data.get("value", "UNKNOWN")

                    # 채팅 메시지 알림은 DB에 저장하지 않음 (FCM만 전송)
                    if notification_value == "CHAT_MESSAGE_RECEIVED":
                        logger.info(
                            f"채팅 메시지 알림은 DB에 저장하지 않음 (FCM만 전송): user_id={user_id}"
                        )
                        return True

                    if (
                        notification_type == "UNKNOWN"
                        or notification_value == "UNKNOWN"
                    ):
                        logger.warning(
                            f"FCM data에 필수 필드가 누락되었습니다: type={notification_type}, value={notification_value}"
                        )
                        return True

                    category = get_notification_category(notification_type)

                    # 알림 생성 전 현재 시간 로깅
                    from datetime import datetime, timezone

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

                    # 알림 생성 후 저장된 시간 확인
                    created_at_value = getattr(notification, "created_at", None)
                    created_at_str = (
                        created_at_value.isoformat()
                        if created_at_value is not None
                        else "None"
                    )
                    logger.info(
                        f"[알림 생성 후] notification_id={getattr(notification, 'id', 'Unknown')}, user_id={user_id}, "
                        f"notification_value={notification_value}, "
                        f"DB 저장 시간(UTC): {created_at_str}, "
                        f"생성 전 시간(UTC): {before_create.isoformat()}"
                    )
                except Exception as db_error:
                    logger.error(f"알림 DB 저장 실패: {db_error}")
                    # DB 저장 실패해도 FCM은 성공한 것으로 처리

            return True

        except Exception as e:
            error_message = str(e)
            logger.error(f"FCM 알림 전송 실패: {error_message}")

            # 토큰 관련 에러인 경우 특별 처리 (InvalidRegistration만 토큰 무효화)
            if "InvalidRegistration" in error_message:
                logger.warning(f"FCM 토큰이 유효하지 않습니다: {token[:20]}...")
                # DB에서 해당 사용자의 FCM 토큰을 null로 업데이트
                if db is not None:
                    await self._invalidate_token(token, db, user_id)
            elif "Auth error from APNS" in error_message:
                logger.warning(f"APNS 인증 에러 발생 (토큰은 유효함): {token[:20]}...")
                # APNS 에러는 토큰 무효화하지 않음 (인증서/설정 문제일 가능성)

            return False

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
        self, tokens: List[str], title: str, body: str, data: dict | None = None
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
        try:
            # 멀티캐스트 메시지 생성
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                tokens=tokens,
            )

            # 메시지 전송
            response = messaging.send_multicast(message)

            logger.info(
                f"FCM 멀티캐스트 알림 전송 완료: "
                f"성공 {response.success_count}, 실패 {response.failure_count}"
            )

            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
            }

        except Exception as e:
            error_message = str(e)
            logger.error(f"FCM 멀티캐스트 알림 전송 실패: {error_message}")

            # 토큰 관련 에러인 경우 특별 처리
            if (
                "Auth error from APNS" in error_message
                or "InvalidRegistration" in error_message
            ):
                logger.warning(f"FCM 멀티캐스트에서 토큰 에러 발생: {error_message}")
                # 멀티캐스트에서는 개별 토큰 무효화가 어려우므로 로그만 남김

            return {
                "success_count": 0,
                "failure_count": len(tokens),
            }

    # ========== 팟팟 알림 전송 함수 ==========

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

        # 메시지 템플릿에 변수 채우기
        formatted_message = message_template
        for placeholder in placeholders:
            value = kwargs.get(placeholder, "")
            formatted_message = formatted_message.replace(
                f"[{placeholder}]", str(value)
            )

        # data 딕셔너리 생성
        # notification_type의 클래스명을 NotificationType enum 값으로 변환
        notification_type_class = notification_type.__class__.__name__
        main_type = get_notification_main_type(notification_type_class)

        data = {
            "type": main_type,  # POD, FOLLOW 등 (NotificationType enum 값)
            "value": notification_type.name,  # POD_JOIN_REQUEST 등 (UPPER_SNAKE_CASE)
        }

        # relatedId 추가 (camelCase)
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
        # 알림 받을 사용자 ID 추가
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
        # 알림 받을 사용자 ID 추가
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
            related_pod_id=None,  # 팔로우 알림은 파티 무관
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
