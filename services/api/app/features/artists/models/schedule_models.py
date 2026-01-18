"""아티스트 스케줄 관련 모델"""

import enum

from app.core.database import Base
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class ScheduleType(enum.Enum):
    """스케줄 유형 열거형"""

    GENERAL_CONTENT = 1  # 일반 콘텐츠 (영상, 방송 등)
    MUSIC_RELEASE = 2  # 음원/앨범 발매
    BIRTHDAY = 4  # 생일/기념일
    OTHER_EVENT = 5  # 기타 이벤트


class ArtistSchedule(Base):
    """아티스트 스케줄 엔터티"""

    __tablename__ = "artist_schedules"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(
        Integer,
        ForeignKey("artists.id"),
        nullable=True,
        index=True,
        comment="아티스트 ID",
    )
    unit_id = Column(
        Integer,
        ForeignKey("artist_units.id"),
        nullable=True,
        index=True,
        comment="아티스트 유닛 ID",
    )
    artist_ko_name = Column(
        String(100), nullable=False, index=True, comment="아티스트 한글명"
    )
    type = Column(Integer, nullable=False, comment="일정 유형")
    start_time = Column(
        BigInteger, nullable=False, index=True, comment="일정 시작 시간 (밀리초)"
    )
    end_time = Column(BigInteger, nullable=False, comment="일정 종료 시간 (밀리초)")
    text = Column(Text, nullable=True, comment="일정 상세 설명")
    title = Column(String(500), nullable=False, comment="일정 제목")
    channel = Column(String(100), nullable=True, comment="방송 채널")
    location = Column(String(200), nullable=True, comment="장소")

    # 메타데이터
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), comment="수정일시"
    )

    # 관계 설정
    artist = relationship("Artist", back_populates="schedules")
    unit = relationship("ArtistUnit", back_populates="schedules")
    members = relationship(
        "ScheduleMember", back_populates="schedule", cascade="all, delete-orphan"
    )
    contents = relationship(
        "ScheduleContent", back_populates="schedule", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ArtistSchedule(id={self.id}, artist='{self.artist_ko_name}', title='{self.title}')>"


class ScheduleMember(Base):
    """스케줄 참여 멤버 엔터티"""

    __tablename__ = "schedule_members"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(
        Integer, ForeignKey("artist_schedules.id"), nullable=False, comment="스케줄 ID"
    )
    artist_id = Column(
        Integer,
        ForeignKey("artists.id"),
        nullable=True,
        index=True,
        comment="아티스트 ID",
    )
    ko_name = Column(String(50), nullable=False, comment="멤버 한글명")
    en_name = Column(String(50), nullable=False, comment="멤버 영문명")

    # 메타데이터
    created_at = Column(DateTime, default=func.now(), comment="생성일시")

    # 관계 설정
    schedule = relationship("ArtistSchedule", back_populates="members")
    artist = relationship("Artist")

    def __repr__(self):
        return f"<ScheduleMember(id={self.id}, ko_name='{self.ko_name}', en_name='{self.en_name}')>"


class ScheduleContent(Base):
    """스케줄 관련 콘텐츠 엔터티"""

    __tablename__ = "schedule_contents"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(
        Integer, ForeignKey("artist_schedules.id"), nullable=False, comment="스케줄 ID"
    )
    type = Column(String(20), nullable=False, comment="콘텐츠 유형 (video, image)")
    path = Column(String(1000), nullable=False, comment="콘텐츠 경로/URL")
    title = Column(String(500), nullable=True, comment="콘텐츠 제목")

    # 메타데이터
    created_at = Column(DateTime, default=func.now(), comment="생성일시")

    # 관계 설정
    schedule = relationship("ArtistSchedule", back_populates="contents")

    def __repr__(self):
        return (
            f"<ScheduleContent(id={self.id}, type='{self.type}', path='{self.path}')>"
        )
