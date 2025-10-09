import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional, List, Union
import logging
from app.core.config import settings
from app.schemas.notification import (
    PodNotificationType,
    PodStatusNotificationType,
    RecommendNotificationType,
    ReviewNotificationType,
    FollowNotificationType,
)

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

                service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_KEY)

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
        data: Optional[dict] = None,
    ) -> bool:
        """
        FCM 푸시 알림 전송

        Args:
            token: FCM 토큰
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터 (선택사항)

        Returns:
            성공 여부
        """
        try:
            # 메시지 생성
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
            )

            # 메시지 전송
            response = messaging.send(message)
            logger.info(f"FCM 알림 전송 성공: {response}")
            return True

        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: {e}")
            return False

    async def send_multicast_notification(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
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
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
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
            logger.error(f"FCM 멀티캐스트 알림 전송 실패: {e}")
            return {
                "success_count": 0,
                "failure_count": len(tokens),
            }

    # ========== 팟팟 알림 전송 함수 ==========

    def _format_message(
        self,
        notification_type: Union[
            PodNotificationType,
            PodStatusNotificationType,
            RecommendNotificationType,
            ReviewNotificationType,
            FollowNotificationType,
        ],
        **kwargs,
    ) -> tuple[str, Optional[dict]]:
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
        data = {
            "type": type(notification_type).__name__,
            "value": notification_type.name,
        }

        # related_id 추가
        if related_id_key and related_id_key in kwargs:
            data["related_id"] = str(kwargs[related_id_key])

        return formatted_message, data

    # ========== 파티 알림 ==========

    async def send_pod_join_request(
        self, token: str, nickname: str, pod_id: int
    ) -> bool:
        """파티 참여 요청 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_JOIN_REQUEST, nickname=nickname, pod_id=pod_id
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_request_approved(
        self, token: str, party_name: str, pod_id: int
    ) -> bool:
        """파티 참여 요청 승인 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_REQUEST_APPROVED,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_request_rejected(
        self, token: str, party_name: str, pod_id: int
    ) -> bool:
        """파티 참여 요청 거절 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_REQUEST_REJECTED,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_new_member(
        self, token: str, nickname: str, party_name: str, pod_id: int
    ) -> bool:
        """파티 새 멤버 참여 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_NEW_MEMBER,
            nickname=nickname,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_updated(self, token: str, party_name: str, pod_id: int) -> bool:
        """파티 정보 수정 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_UPDATED, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_confirmed(
        self, token: str, party_name: str, pod_id: int
    ) -> bool:
        """파티 확정 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_CONFIRMED, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_canceled(self, token: str, party_name: str, pod_id: int) -> bool:
        """파티 취소 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_CANCELED, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_start_soon(
        self, token: str, party_name: str, pod_id: int
    ) -> bool:
        """파티 시작 1시간 전 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_START_SOON, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_low_attendance(
        self, token: str, party_name: str, pod_id: int
    ) -> bool:
        """파티 마감 임박 알림 전송"""
        body, data = self._format_message(
            PodNotificationType.POD_LOW_ATTENDANCE, party_name=party_name, pod_id=pod_id
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    # ========== 파티 상태 알림 ==========

    async def send_pod_likes_threshold(self, token: str, party_name: str) -> bool:
        """파티 좋아요 10개 달성 알림 전송"""
        body, data = self._format_message(
            PodStatusNotificationType.POD_LIKES_THRESHOLD, party_name=party_name
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_pod_views_threshold(self, token: str, party_name: str) -> bool:
        """파티 조회수 10회 달성 알림 전송"""
        body, data = self._format_message(
            PodStatusNotificationType.POD_VIEWS_THRESHOLD, party_name=party_name
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    # ========== 추천 알림 ==========

    async def send_saved_pod_deadline(
        self, token: str, party_name: str, pod_id: int
    ) -> bool:
        """좋아요한 파티 마감 임박 알림 전송"""
        body, data = self._format_message(
            RecommendNotificationType.SAVED_POD_DEADLINE,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_saved_pod_spot_opened(
        self, token: str, party_name: str, pod_id: int
    ) -> bool:
        """좋아요한 파티에 자리 생김 알림 전송"""
        body, data = self._format_message(
            RecommendNotificationType.SAVED_POD_SPOT_OPENED,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    # ========== 리뷰 알림 ==========

    async def send_review_created(
        self, token: str, nickname: str, party_name: str, review_id: int
    ) -> bool:
        """리뷰 등록 알림 전송"""
        body, data = self._format_message(
            ReviewNotificationType.REVIEW_CREATED,
            nickname=nickname,
            party_name=party_name,
            review_id=review_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_review_reminder_day(self, token: str, party_name: str) -> bool:
        """리뷰 작성 유도 알림 (1일 후) 전송"""
        body, data = self._format_message(
            ReviewNotificationType.REVIEW_REMINDER_DAY, party_name=party_name
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_review_reminder_week(self, token: str, party_name: str) -> bool:
        """리뷰 작성 리마인드 알림 (1주일 후) 전송"""
        body, data = self._format_message(
            ReviewNotificationType.REVIEW_REMINDER_WEEK, party_name=party_name
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_review_others_created(
        self, token: str, nickname: str, review_id: int
    ) -> bool:
        """다른 참여자 리뷰 작성 알림 전송"""
        body, data = self._format_message(
            ReviewNotificationType.REVIEW_OTHERS_CREATED,
            nickname=nickname,
            review_id=review_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    # ========== 팔로우 알림 ==========

    async def send_followed_by_user(
        self, token: str, nickname: str, follow_user_id: int
    ) -> bool:
        """팔로우 알림 전송"""
        body, data = self._format_message(
            FollowNotificationType.FOLLOWED_BY_USER,
            nickname=nickname,
            follow_user_id=follow_user_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )

    async def send_followed_user_created_pod(
        self, token: str, nickname: str, party_name: str, pod_id: int
    ) -> bool:
        """팔로우한 유저의 파티 생성 알림 전송"""
        body, data = self._format_message(
            FollowNotificationType.FOLLOWED_USER_CREATED_POD,
            nickname=nickname,
            party_name=party_name,
            pod_id=pod_id,
        )
        return await self.send_notification(
            token=token, title="PodPod", body=body, data=data
        )
