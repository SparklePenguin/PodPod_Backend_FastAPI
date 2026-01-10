"""사용자 기본 모델"""

from datetime import datetime, timezone
from enum import Enum

from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


class UserState(str, Enum):
    """사용자 온보딩 상태"""

    PREFERRED_ARTISTS = "PREFERRED_ARTISTS"  # 선호 아티스트 설정 필요
    TENDENCY_TEST = "TENDENCY_TEST"  # 성향 테스트 필요
    PROFILE_SETTING = "PROFILE_SETTING"  # 프로필 설정 필요
    COMPLETED = "COMPLETED"  # 온보딩 완료


class User(Base):
    """사용자 모델 (소셜 로그인 지원)"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(50), nullable=True)
    intro = Column(String(200), nullable=True)
    profile_image = Column(String(500))  # 프로필 이미지 URL
    tendency_type = Column(String(50), nullable=True)  # 덕메 성향 타입
    hashed_password = Column(String(255), nullable=True)  # 소셜 로그인의 경우 nullable
    state = Column(
        SQLEnum(UserState), default=UserState.PREFERRED_ARTISTS
    )  # 사용자 온보딩 상태
    is_active = Column(Boolean, default=True)
    is_del = Column(Boolean, default=False, index=True)  # 소프트 삭제 플래그
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 소셜 로그인 관련 필드
    auth_provider = Column(String(20), nullable=True)  # 'kakao', 'google', 'apple'
    auth_provider_id = Column(
        String(100), unique=True, index=True, nullable=True
    )  # 소셜 제공자의 고유 ID

    # 관계 설정
    detail = relationship("UserDetail", back_populates="user", uselist=False)
    preferred_artists = relationship("PreferredArtist", back_populates="user")
    notification_settings = relationship(
        "UserNotificationSettings", back_populates="user", uselist=False
    )

    # 팔로우 관계
    following = relationship(
        "Follow", foreign_keys="Follow.follower_id", back_populates="follower"
    )
    followers = relationship(
        "Follow", foreign_keys="Follow.following_id", back_populates="following"
    )

    # 차단 관계
    blocking = relationship(
        "UserBlock", foreign_keys="UserBlock.blocker_id", back_populates="blocker"
    )
    blocked_by = relationship(
        "UserBlock", foreign_keys="UserBlock.blocked_id", back_populates="blocked"
    )

    # 파티 후기 관계
    pod_reviews = relationship("PodReview", back_populates="user")

    # 알림 관계
    notifications = relationship(
        "Notification", foreign_keys="Notification.user_id", back_populates="user"
    )


class PreferredArtist(Base):
    """사용자와 아티스트 관계 모델"""

    __tablename__ = "preferred_artists"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, index=True)

    user = relationship("User", back_populates="preferred_artists")
    artist = relationship("Artist", back_populates="preferred_artists")


class UserDetail(Base):
    """사용자 상세 정보 모델 (리스트 조회 시 제외)"""

    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )

    # 리스트에서 안 쓰는 정보
    username = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)

    # 설정/토큰
    fcm_token = Column(String(500), nullable=True)  # Firebase Cloud Messaging 토큰
    terms_accepted = Column(Boolean, default=False, nullable=False)  # 약관 동의 여부

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 관계 설정
    user = relationship("User", back_populates="detail")
