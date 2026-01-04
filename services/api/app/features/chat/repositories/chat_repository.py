"""
채팅 메시지 Repository
"""

import logging
from datetime import datetime
from typing import List

from app.features.chat.models.chat_models import ChatMessage
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class ChatRepository:
    """채팅 메시지 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 메시지 생성
    async def create_message(
        self, channel_url: str, user_id: int, message: str, message_type: str = "MESG"
    ) -> ChatMessage:
        """채팅 메시지 생성 (channel_url 기반 - 하위 호환성)"""
        chat_message = ChatMessage(
            channel_url=channel_url,
            user_id=user_id,
            message=message,
            message_type=message_type,
        )
        self._session.add(chat_message)
        await self._session.flush()
        await self._session.refresh(chat_message)
        return chat_message

    async def create_message_by_room_id(
        self, chat_room_id: int, user_id: int, message: str, message_type: str = "MESG"
    ) -> ChatMessage:
        """채팅 메시지 생성 (chat_room_id 기반)"""
        chat_message = ChatMessage(
            chat_room_id=chat_room_id,
            channel_url=None,  # deprecated
            user_id=user_id,
            message=message,
            message_type=message_type,
        )
        self._session.add(chat_message)
        await self._session.flush()
        await self._session.refresh(chat_message)
        return chat_message

    # - MARK: 채널의 메시지 목록 조회
    async def get_messages_by_channel(
        self, channel_url: str, page: int = 1, size: int = 50
    ) -> tuple[List[ChatMessage], int]:
        """채널의 메시지 목록 조회 (페이징, channel_url 기반 - 하위 호환성)"""
        offset = (page - 1) * size

        # 전체 개수 조회
        count_query = select(func.count(ChatMessage.id)).where(ChatMessage.channel_url == channel_url)
        count_result = await self._session.execute(count_query)
        total_count = count_result.scalar() or 0

        # 메시지 목록 조회 (최신순, user 관계 eager load)
        query = (
            select(ChatMessage)
            .options(selectinload(ChatMessage.user))
            .where(ChatMessage.channel_url == channel_url)
            .order_by(desc(ChatMessage.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self._session.execute(query)
        messages = result.scalars().all()

        return list(reversed(messages)), total_count

    async def get_messages_by_room_id(
        self, chat_room_id: int, page: int = 1, size: int = 50
    ) -> tuple[List[ChatMessage], int]:
        """채팅방의 메시지 목록 조회 (페이징, chat_room_id 기반)"""
        offset = (page - 1) * size

        # 전체 개수 조회
        count_query = select(func.count(ChatMessage.id)).where(ChatMessage.chat_room_id == chat_room_id)
        count_result = await self._session.execute(count_query)
        total_count = count_result.scalar() or 0

        # 메시지 목록 조회 (최신순, user 관계 eager load)
        query = (
            select(ChatMessage)
            .options(selectinload(ChatMessage.user))
            .where(ChatMessage.chat_room_id == chat_room_id)
            .order_by(desc(ChatMessage.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self._session.execute(query)
        messages = result.scalars().all()

        return list(reversed(messages)), total_count

    # - MARK: 채널의 마지막 메시지 조회
    async def get_last_message(self, channel_url: str) -> ChatMessage | None:
        """채널의 마지막 메시지 조회 (channel_url 기반 - 하위 호환성)"""
        query = (
            select(ChatMessage)
            .options(selectinload(ChatMessage.user))
            .where(ChatMessage.channel_url == channel_url)
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_last_message_by_room_id(self, chat_room_id: int) -> ChatMessage | None:
        """채팅방의 마지막 메시지 조회 (chat_room_id 기반)"""
        query = (
            select(ChatMessage)
            .options(selectinload(ChatMessage.user))
            .where(ChatMessage.chat_room_id == chat_room_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_unread_count(
        self, chat_room_id: int, last_read_at: datetime | None
    ) -> int:
        """읽지 않은 메시지 수 조회"""
        query = select(ChatMessage).where(ChatMessage.chat_room_id == chat_room_id)
        if last_read_at:
            query = query.where(ChatMessage.created_at > last_read_at)
        result = await self._session.execute(query)
        return len(result.scalars().all())

    # - MARK: 사용자의 채팅방 목록 조회
    async def get_user_channels(self, user_id: int) -> List[str]:
        """사용자가 참여한 채널 URL 목록 조회 (메시지가 있는 채널만)"""
        query = (
            select(ChatMessage.channel_url)
            .where(ChatMessage.user_id == user_id)
            .distinct()
        )
        result = await self._session.execute(query)
        return [row[0] for row in result.all()]

    # - MARK: 채널의 메시지 개수 조회
    async def get_message_count(self, channel_url: str) -> int:
        """채널의 메시지 개수 조회"""
        query = select(func.count(ChatMessage.id)).where(ChatMessage.channel_url == channel_url)
        result = await self._session.execute(query)
        return result.scalar() or 0
