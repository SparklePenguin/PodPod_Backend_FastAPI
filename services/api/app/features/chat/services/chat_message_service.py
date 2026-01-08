"""
채팅 메시지 서비스
메시지 저장, 조회, DTO 변환 담당
"""

import logging
from typing import List

from app.features.chat.repositories.chat_repository import ChatRepository
from app.features.chat.schemas.chat_schemas import ChatMessageDto
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChatMessageService:
    """채팅 메시지 서비스 - 메시지 저장 및 조회 담당"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._chat_repo = ChatRepository(session)
        self._user_repo = UserRepository(session)

    # - MARK: 메시지 저장
    async def create_message(
        self, room_id: int, user_id: int, message: str, message_type: str = "MESG"
    ) -> ChatMessageDto:
        """메시지를 DB에 저장하고 DTO로 반환 (commit은 호출하는 서비스에서 처리)"""
        chat_message = await self._chat_repo.create_message(
            room_id=room_id,
            user_id=user_id,
            message=message,
            message_type=message_type,
        )

        # 사용자 정보 조회
        user = await self._user_repo.get_by_id(user_id)

        # DTO 변환
        return self._to_dto(chat_message, user)

    async def create_message_by_room_id(
        self, chat_room_id: int, user_id: int, message: str, message_type: str = "MESG"
    ) -> ChatMessageDto:
        """채팅방 ID로 메시지를 DB에 저장하고 DTO로 반환 (commit은 호출하는 서비스에서 처리)"""
        chat_message = await self._chat_repo.create_message_by_room_id(
            chat_room_id=chat_room_id,
            user_id=user_id,
            message=message,
            message_type=message_type,
        )

        # 사용자 정보 조회
        user = await self._user_repo.get_by_id(user_id)

        # DTO 변환
        return self._to_dto(chat_message, user)

    # - MARK: 메시지 목록 조회
    async def get_messages(
        self, channel_url: str, page: int = 1, size: int = 50
    ) -> tuple[List[ChatMessageDto], int]:
        """채널의 메시지 목록 조회"""
        messages, total_count = await self._chat_repo.get_messages_by_channel(
            channel_url, page, size
        )

        # DTO 변환 (user는 이미 eager load됨)
        message_dtos = [
            self._to_dto(msg, msg.user) for msg in messages
        ]

        return message_dtos, total_count

    async def get_messages_by_room_id(
        self, chat_room_id: int, page: int = 1, size: int = 50
    ) -> tuple[List[ChatMessageDto], int]:
        """채팅방 ID로 메시지 목록 조회"""
        messages, total_count = await self._chat_repo.get_messages_by_room_id(
            chat_room_id, page, size
        )

        # DTO 변환 (user는 이미 eager load됨)
        message_dtos = [
            self._to_dto(msg, msg.user) for msg in messages
        ]

        return message_dtos, total_count

    # - MARK: 마지막 메시지 조회
    async def get_last_message(self, channel_url: str) -> ChatMessageDto | None:
        """채널의 마지막 메시지 조회"""
        last_message_model = await self._chat_repo.get_last_message(channel_url)
        if not last_message_model:
            return None

        # user는 이미 eager load됨
        return self._to_dto(last_message_model, last_message_model.user)

    # - MARK: DTO 변환
    def _to_dto(self, chat_message, user) -> ChatMessageDto:
        """ChatMessage 모델을 DTO로 변환"""
        return ChatMessageDto(
            id=chat_message.id,
            channel_url=chat_message.channel_url,
            user_id=chat_message.user_id,
            nickname=user.nickname if user else None,
            profile_image=user.profile_image if user else None,
            message=chat_message.message,
            message_type=chat_message.message_type,
            created_at=chat_message.created_at,
        )
