"""
채팅 서비스 (Facade)
다양한 채팅 관련 서비스를 조합하여 사용
"""

import logging

from app.core.services.fcm_service import FCMService
from app.core.services.websocket_service import WebSocketService
from app.features.chat.schemas.chat_message_dto import ChatMessageDto
from app.features.chat.services.chat_message_service import ChatMessageService
from app.features.chat.services.chat_notification_service import (
    ChatNotificationService,
)
from app.features.chat.services.chat_pod_service import ChatPodService
from app.features.chat.services.chat_room_service import ChatRoomService
from app.features.chat.services.chat_websocket_service import ChatWebSocketService
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChatService:
    """채팅 서비스 (Facade 패턴) - 다양한 서비스를 조합"""

    def __init__(
        self,
        session: AsyncSession,
        websocket_service: WebSocketService | None = None,
        fcm_service: FCMService | None = None,
    ):
        self._session = session
        self._user_repo = UserRepository(session)

        # 하위 서비스 초기화
        self._websocket_service_wrapper = ChatWebSocketService(websocket_service)
        self._message_service = ChatMessageService(session)
        self._pod_service = ChatPodService(session)
        self._notification_service = ChatNotificationService(
            session=session,
            fcm_service=fcm_service,
            connection_manager=self._websocket_service_wrapper.get_connection_manager(),
        )
        self._room_service = ChatRoomService(
            session=session,
            websocket_service=self._websocket_service_wrapper,
        )

    # - MARK: 메시지 전송
    async def send_message(
        self,
        channel_url: str,
        user_id: int,
        message: str,
        message_type: str = "MESG",
    ) -> ChatMessageDto:
        """메시지 전송 (저장, 브로드캐스트, 알림 전송)"""
        # 1. 메시지 저장
        chat_message_dto = await self._message_service.create_message(
            channel_url=channel_url,
            user_id=user_id,
            message=message,
            message_type=message_type,
        )

        # 2. 사용자 정보 조회
        user = await self._user_repo.get_by_id(user_id)
        sender_name = user.nickname or "알 수 없음" if user else "알 수 없음"

        # 3. 채널 메타데이터 조회
        channel_metadata = await self._websocket_service_wrapper.get_channel_metadata(
            channel_url
        )

        # 4. WebSocket 브로드캐스트
        await self._websocket_service_wrapper.broadcast_message(
            channel_url=channel_url,
            user_id=user_id,
            message=message,
            message_type=message_type,
            timestamp=chat_message_dto.created_at.isoformat(),
        )

        # 5. Pod 정보 추출 및 조회
        pod_id, pod_title = self._pod_service.extract_pod_info_from_metadata(
            channel_metadata, channel_url
        )
        if pod_id:
            pod_title_from_db, simple_pod_dict = await self._pod_service.get_pod_info(
                pod_id
            )
            if pod_title_from_db:
                pod_title = pod_title_from_db
        else:
            simple_pod_dict = None

        # 6. FCM 알림 전송
        await self._notification_service.send_notifications_to_channel(
            channel_url=channel_url,
            sender_id=user_id,
            sender_name=sender_name,
            message=message,
            pod_id=pod_id,
            pod_title=pod_title
            or (channel_metadata.get("name", "파티") if channel_metadata else "파티"),
            simple_pod_dict=simple_pod_dict,
        )

        return chat_message_dto

    # - MARK: 채널의 메시지 목록 조회
    async def get_messages(
        self, channel_url: str, page: int = 1, size: int = 50
    ) -> tuple[list[ChatMessageDto], int]:
        """채널의 메시지 목록 조회"""
        return await self._message_service.get_messages(channel_url, page, size)

    # - MARK: 사용자의 채팅방 목록 조회
    async def get_user_chat_rooms(self, user_id: int) -> list:
        """사용자가 참여한 채팅방 목록 조회"""
        return await self._room_service.get_user_chat_rooms(user_id)
