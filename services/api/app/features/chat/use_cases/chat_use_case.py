"""Chat Use Case - 비즈니스 로직 처리"""

from app.features.chat.exceptions import (
    ChatMemberNotFoundException,
    ChatRoomAccessDeniedException,
    ChatRoomNotFoundException,
)
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.chat.schemas.chat_schemas import ChatMessageDto, ChatRoomDto
from app.features.chat.services.chat_service import ChatService
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession


class ChatUseCase:
    """Chat 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        chat_service: ChatService,
        chat_room_repo: ChatRoomRepository,
    ):
        self._session = session
        self._chat_service = chat_service
        self._chat_room_repo = chat_room_repo

    # MARK: - 메시지 전송
    async def send_message_by_room_id(
        self,
        chat_room_id: int,
        user_id: int,
        message: str,
        message_type: str = "MESG",
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

        # 서비스 로직 호출
        try:
            result = await self._chat_service.send_message_by_room_id(
                chat_room_id=chat_room_id,
                user_id=user_id,
                message=message,
                message_type=message_type,
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 채팅방 상세 조회
    async def get_chat_room_detail(
        self, chat_room_id: int, user_id: int
    ) -> ChatRoomDto:
        """채팅방 상세 정보 조회 (비즈니스 로직 검증)"""
        # 채팅방 존재 확인
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ChatRoomNotFoundException(chat_room_id)

        # 사용자가 멤버인지 확인
        member = await self._chat_room_repo.get_member(chat_room_id, user_id)
        if not member or member.left_at:
            raise ChatRoomAccessDeniedException(chat_room_id, user_id)

        # 서비스 로직 호출
        return await self._chat_service.get_chat_room_detail(chat_room_id, user_id)

    # MARK: - 채팅방 나가기
    async def leave_chat_room(self, chat_room_id: int, user_id: int) -> None:
        """채팅방 나가기 (비즈니스 로직 검증)"""
        # 채팅방 존재 확인
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ChatRoomNotFoundException(chat_room_id)

        # 사용자가 멤버인지 확인
        member = await self._chat_room_repo.get_member(chat_room_id, user_id)
        if not member or member.left_at:
            raise ChatMemberNotFoundException(chat_room_id, user_id)

        # 서비스 로직 호출
        try:
            await self._chat_service.leave_chat_room(chat_room_id, user_id)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 읽음 처리
    async def mark_as_read(self, chat_room_id: int, user_id: int) -> None:
        """채팅방 읽음 처리 (비즈니스 로직 검증)"""
        # 채팅방 존재 확인
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ChatRoomNotFoundException(chat_room_id)

        # 사용자가 멤버인지 확인
        member = await self._chat_room_repo.get_member(chat_room_id, user_id)
        if not member or member.left_at:
            raise ChatRoomAccessDeniedException(chat_room_id, user_id)

        # 서비스 로직 호출
        try:
            await self._chat_service.mark_as_read(chat_room_id, user_id)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 메시지 목록 조회
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
        return await self._chat_service.get_messages_by_room_id(chat_room_id, page, size)

    # MARK: - 채팅방 목록 조회
    async def get_user_chat_rooms(self, user_id: int) -> list[ChatRoomDto]:
        """사용자가 참여한 채팅방 목록 조회"""
        return await self._chat_service.get_user_chat_rooms(user_id)

    # MARK: - WebSocket 연결 처리
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        channel_url: str,
        user_id: int,
    ) -> None:
        """WebSocket 연결 처리 (비즈니스 로직 검증)"""
        # 채팅방 ID 추출 (channel_url에서)
        if channel_url.startswith("chat_room_"):
            try:
                chat_room_id = int(channel_url.replace("chat_room_", ""))
                # 채팅방 존재 확인
                chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
                if not chat_room:
                    await websocket.close(code=1003)
                    raise ChatRoomNotFoundException(chat_room_id)

                # 사용자가 멤버인지 확인
                member = await self._chat_room_repo.get_member(chat_room_id, user_id)
                if not member or member.left_at:
                    await websocket.close(code=1008)
                    raise ChatRoomAccessDeniedException(chat_room_id, user_id)
            except ValueError:
                # channel_url 형식이 잘못된 경우
                await websocket.close(code=1003)
                raise ChatRoomNotFoundException(0)

        # 서비스 로직 호출
        await self._chat_service.handle_websocket_connection(
            websocket=websocket,
            channel_url=channel_url,
            user_id=user_id,
        )
