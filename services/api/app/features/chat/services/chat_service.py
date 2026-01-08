"""
채팅 서비스 (Facade)
다양한 채팅 관련 서비스를 조합하여 사용
"""

import logging

from app.core.services.fcm_service import FCMService
from app.features.chat.enums import MessageType
from app.features.chat.schemas.chat_schemas import ChatMessageDto, ChatRoomDto
from app.features.chat.services.chat_message_service import ChatMessageService
from app.features.chat.services.chat_notification_service import (
    ChatNotificationService,
)
from app.features.chat.services.chat_pod_service import ChatPodService
from app.features.chat.services.chat_room_service import ChatRoomService
from app.features.chat.services.websocket_service import WebSocketService
from app.features.users.repositories import UserRepository
from fastapi import WebSocket
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
        self._websocket_service = websocket_service
        self._message_service = ChatMessageService(session)
        self._pod_service = ChatPodService(session)
        self._notification_service = ChatNotificationService(
            session=session,
            fcm_service=fcm_service,
            connection_manager=websocket_service.get_connection_manager()
            if websocket_service
            else None,
        )
        self._room_service = ChatRoomService(session=session)

    # - MARK: 메시지 전송
    async def send_message(
        self,
        room_id: int,
        user_id: int,
        message: str,
        message_type: MessageType = MessageType.TEXT,
    ) -> ChatMessageDto:
        """메시지 전송 (저장, 브로드캐스트, 알림 전송)"""
        # 1. 메시지 저장
        chat_message_dto = await self._message_service.create_message(
            room_id=room_id,
            user_id=user_id,
            message=message,
            message_type=message_type,
        )

        # 2. commit은 use_case에서 처리

        # 2. 사용자 정보 조회
        user = await self._user_repo.get_by_id(user_id)
        sender_name = user.nickname or "알 수 없음" if user else "알 수 없음"

        # 3. 채널 메타데이터 조회
        channel_metadata = None
        if self._websocket_service:
            channel_metadata = await self._websocket_service.get_channel_metadata(
                room_id
            )

        # 4. WebSocket 브로드캐스트 (전체 DTO 전달)
        if self._websocket_service:
            await self._websocket_service.broadcast_message_dto(
                room_id=room_id,
                message_dto=chat_message_dto,
            )

        # 5. Pod 정보 추출 및 조회
        pod_id, pod_title = self._pod_service.extract_pod_info_from_metadata(
            channel_metadata, room_id
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
            room_id=room_id,
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

    # - MARK: 채팅방 상세 조회
    async def get_chat_room_detail(
        self, chat_room_id: int, user_id: int
    ) -> ChatRoomDto | None:
        """채팅방 상세 정보 조회"""
        return await self._room_service.get_chat_room_detail(chat_room_id, user_id)

    # - MARK: 채팅방 나가기
    async def leave_chat_room(self, chat_room_id: int, user_id: int) -> bool:
        """채팅방 나가기"""
        return await self._room_service.leave_chat_room(chat_room_id, user_id)

    # - MARK: 읽음 처리
    async def mark_as_read(self, chat_room_id: int, user_id: int) -> bool:
        """채팅방 읽음 처리"""
        return await self._room_service.mark_as_read(chat_room_id, user_id)

    # - MARK: 채팅방 ID로 메시지 목록 조회
    async def get_messages_by_room_id(
        self, chat_room_id: int, page: int = 1, size: int = 50
    ) -> tuple[list[ChatMessageDto], int]:
        """채팅방 ID로 메시지 목록 조회"""
        return await self._message_service.get_messages_by_room_id(
            chat_room_id, page, size
        )

    # - MARK: 채팅방 ID로 메시지 전송
    async def send_message_by_room_id(
        self,
        chat_room_id: int,
        user_id: int,
        message: str,
        message_type: MessageType = MessageType.TEXT,
    ) -> ChatMessageDto:
        """채팅방 ID로 메시지 전송 (검증은 use case에서 처리, commit은 use case에서 처리)"""
        # 1. 메시지 저장
        chat_message_dto = await self._message_service.create_message_by_room_id(
            chat_room_id=chat_room_id,
            user_id=user_id,
            message=message,
            message_type=message_type,
        )

        # 2. commit은 use_case에서 처리

        # 3. 사용자 정보 조회
        user = await self._user_repo.get_by_id(user_id)
        sender_name = user.nickname or "알 수 없음" if user else "알 수 없음"

        # 4. 채팅방 정보 조회
        from app.features.chat.repositories.chat_room_repository import (
            ChatRoomRepository,
        )

        chat_room_repo = ChatRoomRepository(self._session)
        chat_room = await chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            return chat_message_dto

        # 5. WebSocket 브로드캐스트 (전체 DTO 전달)
        if self._websocket_service:
            await self._websocket_service.broadcast_message_dto(
                room_id=chat_room_id,
                message_dto=chat_message_dto,
            )

        # 6. Pod 정보 조회
        pod_id = chat_room.pod_id
        pod_title = None
        simple_pod_dict = None
        if pod_id:
            pod_title_from_db, simple_pod_dict = await self._pod_service.get_pod_info(
                pod_id
            )
            if pod_title_from_db:
                pod_title = pod_title_from_db

        # 6. FCM 알림 전송
        await self._notification_service.send_notifications_to_channel(
            room_id=chat_room_id,
            sender_id=user_id,
            sender_name=sender_name,
            message=message,
            pod_id=pod_id,
            pod_title=pod_title or chat_room.name,
            simple_pod_dict=simple_pod_dict,
        )

        return chat_message_dto

    # - MARK: WebSocket 연결 처리
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        room_id: int,
        user_id: int,
    ) -> None:
        """WebSocket 연결 처리 및 메시지 수신 루프"""

        async def on_message(message_text: str, message_type: MessageType):
            """메시지 수신 시 처리"""
            try:
                await self.send_message(
                    room_id=room_id,
                    user_id=user_id,
                    message=message_text,
                    message_type=message_type,
                )
                # WebSocket에서 메시지 전송 시 commit 필요
                await self._session.commit()
            except Exception as e:
                await self._session.rollback()
                logger.error(f"WebSocket 메시지 전송 실패: {e}", exc_info=True)
                # 예외가 발생해도 WebSocket 연결 유지

        if self._websocket_service:
            await self._websocket_service.handle_websocket_connection(
                websocket=websocket,
                room_id=room_id,
                user_id=user_id,
                on_message=on_message,
            )
        else:
            logger.error("[WebSocket] websocket_service가 None입니다!")
