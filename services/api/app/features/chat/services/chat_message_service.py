"""
채팅 메시지 서비스
메시지 저장, 조회, DTO 변환 담당
"""

import logging
from typing import List

from app.features.chat.repositories.chat_repository import ChatRepository
from app.features.chat.schemas.chat_message_dto import ChatMessageDto
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
        self, channel_url: str, user_id: int, message: str, message_type: str = "MESG"
    ) -> ChatMessageDto:
        """메시지를 DB에 저장하고 DTO로 반환"""
        chat_message = await self._chat_repo.create_message(
            channel_url=channel_url,
            user_id=user_id,
            message=message,
            message_type=message_type,
        )
        await self._session.commit()

        # 사용자 정보 조회
        user = await self._user_repo.get_by_id(user_id)

        # DTO 변환
        return self._to_dto(chat_message, user)

    # - MARK: 메시지 목록 조회
    async def get_messages(
        self, channel_url: str, page: int = 1, size: int = 50
    ) -> tuple[List[ChatMessageDto], int]:
        """채널의 메시지 목록 조회 (N+1 문제 해결)"""
        messages, total_count = await self._chat_repo.get_messages_by_channel(
            channel_url, page, size
        )

        # 사용자 ID 목록 추출
        user_ids = list(set(msg.user_id for msg in messages))

        # 한 번의 쿼리로 모든 사용자 정보 조회
        users_dict = {}
        if user_ids:
            from app.features.users.models import User
            from sqlalchemy import select

            query = select(User).where(User.id.in_(user_ids))
            result = await self._session.execute(query)
            users = result.scalars().all()
            users_dict = {user.id: user for user in users if user.id}

        # DTO 변환
        message_dtos = [
            self._to_dto(msg, users_dict.get(msg.user_id)) for msg in messages
        ]

        return message_dtos, total_count

    # - MARK: 마지막 메시지 조회
    async def get_last_message(self, channel_url: str) -> ChatMessageDto | None:
        """채널의 마지막 메시지 조회"""
        last_message_model = await self._chat_repo.get_last_message(channel_url)
        if not last_message_model:
            return None

        user = await self._user_repo.get_by_id(last_message_model.user_id)
        return self._to_dto(last_message_model, user)

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
