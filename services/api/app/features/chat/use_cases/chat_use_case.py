"""Chat Use Case - 비즈니스 로직 처리"""

import logging

from app.features.chat.enums import MessageType
from app.features.chat.exceptions import (
    ChatRoomAccessDeniedException,
    ChatRoomNotFoundException,
)
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.chat.schemas.chat_schemas import ChatMessageDto
from app.features.chat.services.chat_message_service import ChatMessageService
from app.features.chat.services.chat_notification_service import ChatNotificationService
from app.features.chat.services.chat_pod_service import ChatPodService
from app.features.chat.services.websocket_service import WebSocketService
from app.features.users.repositories import UserRepository
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChatUseCase:
    """Chat 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        chat_room_repo: ChatRoomRepository,
        message_service: ChatMessageService,
        pod_service: ChatPodService,
        notification_service: ChatNotificationService,
        websocket_service: WebSocketService | None = None,
    ) -> None:
        """
        Args:
            session: 데이터베이스 세션
            user_repo: 사용자 레포지토리
            chat_room_repo: 채팅방 레포지토리
            message_service: 채팅 메시지 서비스
            pod_service: Pod 서비스
            notification_service: 알림 서비스
            websocket_service: WebSocket 서비스 (선택적)
        """
        self._session = session
        self._user_repo = user_repo
        self._chat_room_repo = chat_room_repo
        self._message_service = message_service
        self._pod_service = pod_service
        self._notification_service = notification_service
        self._websocket_service = websocket_service

    # MARK: - 메시지 전송 (room_id 기준)
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
        pod_id, pod_title = ChatPodService.extract_pod_info_from_metadata(
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

    # MARK: - 메시지 전송 (채팅방 ID 기준, 검증 포함)
    async def send_message_by_room_id(
        self,
        chat_room_id: int,
        user_id: int,
        message: str,
        message_type: MessageType = MessageType.TEXT,
    ) -> ChatMessageDto:
        """채팅방 ID로 메시지 전송 (비즈니스 로직 검증)"""
        # 채팅방 존재 확인
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ChatRoomNotFoundException(chat_room_id)

        # 사용자가 멤버인지 확인
        member = await self._chat_room_repo.get_member(chat_room_id, user_id)
        if not member or member.left_at:
            raise ChatRoomAccessDeniedException(chat_room_id, user_id)

        try:
            # 1. 메시지 저장
            chat_message_dto = await self._message_service.create_message_by_room_id(
                chat_room_id=chat_room_id,
                user_id=user_id,
                message=message,
                message_type=message_type,
            )

            # 2. 사용자 정보 조회
            user = await self._user_repo.get_by_id(user_id)
            sender_name = user.nickname or "알 수 없음" if user else "알 수 없음"

            # 3. WebSocket 브로드캐스트 (전체 DTO 전달)
            if self._websocket_service:
                await self._websocket_service.broadcast_message_dto(
                    room_id=chat_room_id,
                    message_dto=chat_message_dto,
                )

            # 4. Pod 정보 조회
            pod_id = chat_room.pod_id
            pod_title = None
            simple_pod_dict = None
            if pod_id:
                (
                    pod_title_from_db,
                    simple_pod_dict,
                ) = await self._pod_service.get_pod_info(pod_id)
                if pod_title_from_db:
                    pod_title = pod_title_from_db

            # 5. FCM 알림 전송
            await self._notification_service.send_notifications_to_channel(
                room_id=chat_room_id,
                sender_id=user_id,
                sender_name=sender_name,
                message=message,
                pod_id=pod_id,
                pod_title=pod_title or chat_room.name,
                simple_pod_dict=simple_pod_dict,
            )

            await self._session.commit()
            return chat_message_dto
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 채널의 메시지 목록 조회
    async def get_messages(
        self, channel_url: str, page: int = 1, size: int = 50
    ) -> tuple[list[ChatMessageDto], int]:
        """채널의 메시지 목록 조회"""
        return await self._message_service.get_messages(channel_url, page, size)

    # MARK: - 채팅방 ID로 메시지 목록 조회
    async def get_messages_by_room_id(
        self, chat_room_id: int, user_id: int, page: int = 1, size: int = 50
    ) -> tuple[list[ChatMessageDto], int]:
        """채팅방 ID로 메시지 목록 조회 (비즈니스 로직 검증)"""
        # 채팅방 존재 확인
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ChatRoomNotFoundException(chat_room_id)

        # 사용자가 멤버인지 확인
        member = await self._chat_room_repo.get_member(chat_room_id, user_id)
        if not member or member.left_at:
            raise ChatRoomAccessDeniedException(chat_room_id, user_id)

        # 서비스 로직 호출
        return await self._message_service.get_messages_by_room_id(
            chat_room_id, page, size
        )

    # MARK: - WebSocket 연결 처리
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        room_id: int,
        user_id: int,
    ) -> None:
        """WebSocket 연결 처리 (비즈니스 로직 검증)"""
        # 채팅방 존재 확인
        chat_room = await self._chat_room_repo.get_chat_room_by_id(room_id)
        if not chat_room:
            await websocket.close(code=1003)
            logger.warning(f"채팅방을 찾을 수 없음: room_id={room_id}")
            return

        # 사용자가 멤버인지 확인
        member = await self._chat_room_repo.get_member(room_id, user_id)
        if not member or member.left_at:
            await websocket.close(code=1008)
            logger.warning(f"채팅방 접근 거부: room_id={room_id}, user_id={user_id}")
            return

        # 채널 메타데이터가 없으면 생성 (WebSocket 연결 전)
        if self._websocket_service:
            channel_metadata = await self._websocket_service.get_channel_metadata(
                room_id
            )
            if not channel_metadata:
                # 활성 멤버 목록 조회
                active_members = await self._chat_room_repo.get_active_members(room_id)
                member_ids = [m.user_id for m in active_members]

                # 채널 메타데이터 생성
                await self._websocket_service.create_channel(
                    room_id=room_id,
                    name=chat_room.name,
                    user_ids=member_ids,
                    cover_url=chat_room.cover_url,
                    data={"pod_id": chat_room.pod_id} if chat_room.pod_id else None,
                )
                logger.info(f"채널 메타데이터 자동 생성: room_id={room_id}")

        async def on_message(message_text: str, message_type: MessageType) -> None:
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

        # WebSocket 연결 처리
        if self._websocket_service:
            await self._websocket_service.handle_websocket_connection(
                websocket=websocket,
                room_id=room_id,
                user_id=user_id,
                on_message=on_message,
            )
        else:
            logger.error("[WebSocket] websocket_service가 None입니다!")

    # MARK: - WebSocket 서비스 접근자
    def get_websocket_service(self) -> WebSocketService | None:
        """WebSocket 서비스 반환 (외부에서 접근 필요 시)"""
        return self._websocket_service
