"""
채팅 메시지 모델
"""

from datetime import datetime, timezone

from app.core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class ChatMessage(Base):
    """채팅 메시지 모델"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_room_id = Column(
        Integer,
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="채팅방 ID",
    )
    # channel_url은 deprecated (chat_room_id 사용)
    channel_url = Column(
        String(255),
        nullable=True,
        index=True,
        comment="채널 URL (deprecated - chat_room_id 사용)",
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="발신자 ID"
    )
    message = Column(Text, nullable=False, comment="메시지 내용")
    message_type = Column(
        String(20),
        nullable=False,
        default="MESG",
        comment="메시지 타입 (MESG, FILE, IMAGE 등)",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
        index=True,
    )

    # 관계 설정
    chat_room = relationship("ChatRoom", back_populates="messages", foreign_keys=[chat_room_id])
    user = relationship("User", foreign_keys=[user_id])
