from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Float,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy import Date, Time, Text
from app.core.database import Base
from .pod_status import PodStatus


class Pod(Base):
    __tablename__ = "pods"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    selected_artist_id = Column(
        Integer,
        ForeignKey("artists.id"),
        nullable=True,
        index=True,
    )
    title = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    sub_categories = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=False)
    place = Column(String(200), nullable=False)
    address = Column(String(300), nullable=False)
    sub_address = Column(String(300), nullable=True)
    x = Column(Float, nullable=True, comment="경도 (longitude)")
    y = Column(Float, nullable=True, comment="위도 (latitude)")
    meeting_date = Column(Date, nullable=False)
    meeting_time = Column(Time, nullable=False)
    status = Column(Enum(PodStatus), default=PodStatus.RECRUITING, nullable=False)
    chat_channel_url = Column(String(255), nullable=True, comment="Sendbird 채팅방 URL")
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = relationship("User")
    members = relationship(
        "PodMember",
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    ratings = relationship(
        "PodRating",
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    views = relationship(
        "PodView",
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    applications = relationship(
        "PodApplication",
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    reviews = relationship(
        "PodReview",
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    images = relationship(
        "PodImage",
        back_populates="pod",
        cascade="all, delete-orphan",
    )
