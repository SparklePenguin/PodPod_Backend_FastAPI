"""
채팅 관련 모델들
"""

from datetime import datetime, timezone

from app.core.database import Base
from app.features.chat.enums import MessageType
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


class ChatRoom(Base):
    """채팅방 모델"""

    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(
        Integer,
        ForeignKey("pods.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="파티 ID (1:1 관계, Pod.chat_room_id와 양방향 관계)",
    )
    name = Column(String(100), nullable=False, comment="채팅방 이름")
    cover_url = Column(String(500), nullable=True, comment="채팅방 커버 이미지 URL")
    room_metadata = Column(Text, nullable=True, comment="채팅방 메타데이터 (JSON)")
    is_del = Column(Boolean, default=True, nullable=False, comment="활성화 여부")
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="생성 시간",
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="수정 시간",
    )

    # 관계 설정
    pod = relationship("Pod", foreign_keys=[pod_id])
    members = relationship(
        "ChatMember",
        back_populates="chat_room",
        cascade="all, delete-orphan",
    )
    messages = relationship(
        "ChatMessage",
        back_populates="chat_room",
        cascade="all, delete-orphan",
    )


class ChatMember(Base):
    """채팅방 멤버 모델"""

    __tablename__ = "chat_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_room_id = Column(
        Integer,
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="채팅방 ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용자 ID",
    )
    role = Column(
        String(20),
        nullable=False,
        default="member",
        comment="역할 (owner, admin, member)",
    )
    joined_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="참여 시간",
    )
    left_at = Column(DateTime, nullable=True, comment="나간 시간 (null이면 참여 중)")
    last_read_at = Column(
        DateTime,
        nullable=True,
        comment="마지막 읽은 시간 (읽지 않은 메시지 수 계산용)",
    )

    # 관계 설정
    chat_room = relationship("ChatRoom", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        UniqueConstraint("chat_room_id", "user_id", name="uq_chat_members_room_user"),
    )


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
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="발신자 ID"
    )
    message = Column(Text, nullable=False, comment="메시지 내용")
    message_type = Column(
        Enum(MessageType),
        nullable=False,
        default=MessageType.TEXT,
        comment="메시지 타입 (TEXT, FILE, IMAGE 등)",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # 관계 설정
    chat_room = relationship(
        "ChatRoom", back_populates="messages", foreign_keys=[chat_room_id]
    )
    user = relationship("User", foreign_keys=[user_id])
