"""
채팅방 서비스
채팅방 목록 조회 및 정보 조회 담당
"""

import logging
from datetime import datetime as dt
from typing import List

from app.features.chat.repositories.chat_repository import ChatRepository
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.chat.schemas.chat_schemas import ChatRoomDto
from app.features.chat.services.chat_message_service import ChatMessageService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChatRoomService:
    """채팅방 서비스 - 채팅방 목록 조회 및 정보 조회 담당"""

    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session
        self._chat_room_repo = ChatRoomRepository(session)
        self._chat_repo = ChatRepository(session)
        self._message_service = ChatMessageService(session)

    # - MARK: 사용자의 채팅방 목록 조회
    async def get_user_chat_rooms(self, user_id: int) -> List[ChatRoomDto]:
        """사용자가 참여한 채팅방 목록 조회 (DB 기반)"""
        # DB에서 사용자가 참여한 채팅방 목록 조회
        chat_rooms = await self._chat_room_repo.get_user_chat_rooms(user_id)

        rooms = []
        for chat_room in chat_rooms:
            # 활성 멤버 수 조회
            active_members = await self._chat_room_repo.get_active_members(chat_room.id)
            member_count = len(active_members)

            # 마지막 메시지 조회
            last_message_model = await self._get_last_message_by_room_id(chat_room.id)
            last_message = None
            if last_message_model:
                last_message = self._message_service._to_dto(last_message_model, last_message_model.user)

            # Pod 정보 조회
            pod_id = chat_room.pod_id
            pod_title = None
            if chat_room.pod:
                pod_title = chat_room.pod.title

            # channel_url 생성 (기존 호환성을 위해)
            channel_url = f"chat_room_{chat_room.id}"

            rooms.append(
                ChatRoomDto(
                    channel_url=channel_url,
                    name=chat_room.name,
                    cover_url=chat_room.cover_url,
                    pod_id=pod_id,
                    pod_title=pod_title,
                    member_count=member_count,
                    last_message=last_message,
                    unread_count=await self._chat_room_repo.get_unread_count(chat_room.id, user_id),
                    created_at=chat_room.created_at.isoformat() if chat_room.created_at else "",
                )
            )

        # 마지막 메시지 시간 기준으로 정렬
        rooms.sort(
            key=lambda r: r.last_message.created_at
            if r.last_message
            else dt.min,
            reverse=True,
        )

        return rooms

    # - MARK: 채팅방 상세 조회
    async def get_chat_room_detail(
        self, chat_room_id: int, user_id: int
    ) -> ChatRoomDto:
        """채팅방 상세 정보 조회 (검증은 use case에서 처리)"""

        # 채팅방 조회
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ValueError(f"채팅방을 찾을 수 없습니다: {chat_room_id}")

        # 활성 멤버 수 조회
        active_members = await self._chat_room_repo.get_active_members(chat_room_id)
        member_count = len(active_members)

        # 마지막 메시지 조회
        last_message_model = await self._get_last_message_by_room_id(chat_room_id)
        last_message = None
        if last_message_model:
            last_message = self._message_service._to_dto(last_message_model, last_message_model.user)

        # Pod 정보 조회
        pod_id = chat_room.pod_id
        pod_title = None
        if chat_room.pod:
            pod_title = chat_room.pod.title

        # 읽지 않은 메시지 수 조회
        unread_count = await self._chat_room_repo.get_unread_count(chat_room_id, user_id)

        # channel_url 생성 (기존 호환성을 위해)
        channel_url = f"chat_room_{chat_room_id}"

        return ChatRoomDto(
            channel_url=channel_url,
            name=chat_room.name,
            cover_url=chat_room.cover_url,
            pod_id=pod_id,
            pod_title=pod_title,
            member_count=member_count,
            last_message=last_message,
            unread_count=unread_count,
            created_at=chat_room.created_at.isoformat() if chat_room.created_at else "",
        )

    # - MARK: 채팅방 나가기
    async def leave_chat_room(self, chat_room_id: int, user_id: int) -> None:
        """채팅방 나가기 (검증은 use case에서 처리, commit은 use case에서 처리)"""
        await self._chat_room_repo.remove_member(chat_room_id, user_id)

    # - MARK: 읽음 처리
    async def mark_as_read(self, chat_room_id: int, user_id: int) -> None:
        """채팅방 읽음 처리 (검증은 use case에서 처리, commit은 use case에서 처리)"""
        await self._chat_room_repo.update_last_read_at(chat_room_id, user_id)

    # - MARK: 채팅방의 마지막 메시지 조회
    async def _get_last_message_by_room_id(self, chat_room_id: int):
        """채팅방 ID로 마지막 메시지 조회"""
        return await self._chat_repo.get_last_message_by_room_id(chat_room_id)
