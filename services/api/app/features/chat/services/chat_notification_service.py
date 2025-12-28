"""
채팅 알림 서비스
FCM 알림 전송 담당
"""

import json
import logging

from app.core.services.fcm_service import FCMService
from app.core.services.websocket_service import ConnectionManager
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChatNotificationService:
    """채팅 알림 서비스 - FCM 알림 전송 담당"""

    def __init__(
        self,
        session: AsyncSession,
        fcm_service: FCMService | None = None,
        connection_manager: ConnectionManager | None = None,
    ):
        self._session = session
        self._user_repo = UserRepository(session)
        self._fcm_service = fcm_service or FCMService()
        self._connection_manager = connection_manager

    # - MARK: 채널 멤버에게 FCM 알림 전송
    async def send_notifications_to_channel(
        self,
        channel_url: str,
        sender_id: int,
        sender_name: str,
        message: str,
        pod_id: int | None = None,
        pod_title: str = "파티",
        simple_pod_dict: dict | None = None,
    ) -> None:
        """채널의 모든 멤버에게 FCM 알림 전송 (접속 중이면 제외)"""
        if not self._connection_manager:
            logger.warning("ConnectionManager가 없어 FCM 알림을 전송할 수 없습니다.")
            return

        # 채널 멤버 조회
        members = self._connection_manager.get_channel_members(channel_url)
        if not members:
            return

        # 각 멤버에게 알림 전송
        for member_id in members:
            if member_id == sender_id:
                continue  # 발신자 제외

            # 접속 중이면 FCM 전송 안 함
            if self._connection_manager.is_user_in_channel(channel_url, member_id):
                continue

            await self._send_fcm_notification(
                recipient_id=member_id,
                sender_name=sender_name,
                message=message,
                channel_url=channel_url,
                pod_id=pod_id,
                pod_title=pod_title,
                simple_pod_dict=simple_pod_dict,
            )

    # - MARK: FCM 알림 전송
    async def _send_fcm_notification(
        self,
        recipient_id: int,
        sender_name: str,
        message: str,
        channel_url: str,
        pod_id: int | None = None,
        pod_title: str = "파티",
        simple_pod_dict: dict | None = None,
    ) -> None:
        """FCM 알림 전송 (내부 메서드)"""
        try:
            # 수신자 정보 조회
            recipient = await self._user_repo.get_by_id(recipient_id)
            if not recipient or not recipient.fcm_token:
                return

            # 알림 제목: 파티 이름
            title = pod_title

            # 알림 본문: "발송자 이름: 메시지 내용"
            message_preview = message if len(message) <= 60 else message[:57] + "..."
            body = f"{sender_name}: {message_preview}"

            # 알림 데이터
            data = {
                "type": "COMMUNITY",
                "value": "CHAT_MESSAGE_RECEIVED",
                "relatedId": str(pod_id) if pod_id else str(recipient_id),
            }
            if simple_pod_dict:
                data["pod"] = json.dumps(simple_pod_dict, ensure_ascii=False)
            if channel_url:
                data["channelUrl"] = channel_url

            # FCM 전송
            await self._fcm_service.send_notification(
                token=recipient.fcm_token,
                title=title,
                body=body,
                data=data,
                db=self._session,
                user_id=recipient_id,
                related_user_id=None,
                related_pod_id=pod_id,
            )
            logger.info(
                f"채팅 메시지 FCM 알림 전송: recipient_id={recipient_id}, channel_url={channel_url}"
            )

        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: recipient_id={recipient_id}, error={e}")
