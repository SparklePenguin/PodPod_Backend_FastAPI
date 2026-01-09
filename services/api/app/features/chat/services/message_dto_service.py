"""
채팅 메시지 DTO 변환 서비스
ChatMessage 모델을 ChatMessageDto로 변환하는 로직 담당
"""

from app.features.chat.models import ChatMessage
from app.features.chat.schemas.chat_schemas import ChatMessageDto
from app.features.users.models import User


class MessageDtoService:
    """채팅 메시지 DTO 변환 서비스 (Stateless)"""

    @staticmethod
    def convert_to_dto(chat_message: ChatMessage, user: User | None) -> ChatMessageDto:
        """ChatMessage 모델을 DTO로 변환

        Args:
            chat_message: 채팅 메시지 모델
            user: 사용자 모델 (None일 수 있음)

        Returns:
            ChatMessageDto: 변환된 DTO
        """
        return ChatMessageDto(
            id=chat_message.id,
            user_id=chat_message.user_id,
            nickname=user.nickname if user else None,
            profile_image=user.profile_image if user else None,
            message=chat_message.message,
            message_type=chat_message.message_type,
            created_at=chat_message.created_at,
        )
