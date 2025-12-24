from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserState(str, Enum):
    """사용자 온보딩 상태"""

    PREFERRED_ARTISTS = "PREFERRED_ARTISTS"  # 선호 아티스트 설정 필요
    TENDENCY_TEST = "TENDENCY_TEST"  # 성향 테스트 필요
    PROFILE_SETTING = "PROFILE_SETTING"  # 프로필 설정 필요
    COMPLETED = "COMPLETED"  # 온보딩 완료


# 사용자 모델 (소셜 로그인 지원)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String(50), index=True, nullable=True
    )  # 소셜 로그인의 경우 nullable
    email = Column(String(100), index=True, nullable=True)
    nickname = Column(String(50), nullable=True)
    intro = Column(String(200), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # 소셜 로그인의 경우 nullable
    profile_image = Column(String(500))  # 프로필 이미지 URL
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

    # FCM 토큰 (푸시 알림용)
    fcm_token = Column(String(500), nullable=True)  # Firebase Cloud Messaging 토큰

    # 약관 동의
    terms_accepted = Column(Boolean, default=False, nullable=False)  # 약관 동의 여부

    # 관계 설정
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


# 사용자와 아티스트 관계 모델
class PreferredArtist(Base):
    __tablename__ = "preferred_artists"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, index=True)

    user = relationship("User", back_populates="preferred_artists")
    artist = relationship("Artist", back_populates="preferred_artists")


class UserBlock(Base):
    """사용자 차단 모델"""

    __tablename__ = "user_blocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    blocker_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="차단을 수행한 사용자 ID",
    )
    blocked_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="차단당한 사용자 ID",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="차단 생성 시간",
    )

    # 관계 설정
    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="blocking")
    blocked = relationship(
        "User", foreign_keys=[blocked_id], back_populates="blocked_by"
    )

    # 유니크 제약조건: 한 사용자가 같은 사용자를 중복 차단할 수 없음
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="unique_user_block"),
    )


class UserNotificationSettings(Base):
    """사용자 알림 설정 모델"""

    __tablename__ = "user_notification_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )  # 사용자 ID (1:1 관계)

    # 카테고리별 알림 설정
    notice_enabled = Column(
        Boolean, default=True, nullable=False, comment="공지 알림 활성화"
    )
    pod_enabled = Column(
        Boolean, default=True, nullable=False, comment="파티 알림 활성화"
    )
    community_enabled = Column(
        Boolean, default=True, nullable=False, comment="커뮤니티 알림 활성화"
    )
    chat_enabled = Column(
        Boolean, default=True, nullable=False, comment="채팅 알림 활성화"
    )

    # 방해금지 시간 설정
    do_not_disturb_enabled = Column(
        Boolean, default=False, nullable=False, comment="방해금지 모드 활성화"
    )
    do_not_disturb_start = Column(
        Time, nullable=True, comment="방해금지 시작 시간 (HH:MM)"
    )
    do_not_disturb_end = Column(
        Time, nullable=True, comment="방해금지 종료 시간 (HH:MM)"
    )

    # 마케팅 수신 동의
    marketing_enabled = Column(
        Boolean, default=False, nullable=False, comment="마케팅 알림 수신 동의"
    )

    # 관계 설정
    user = relationship("User", back_populates="notification_settings")


class UserReport(Base):
    """사용자 신고 모델"""

    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reporter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="신고를 수행한 사용자 ID",
    )
    reported_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="신고당한 사용자 ID",
    )
    report_types = Column(
        JSON,
        nullable=False,
        comment="신고 유형 ID 목록 (최대 3개)",
    )
    reason = Column(
        String(500),
        nullable=True,
        comment="신고 이유 (추가 설명)",
    )
    blocked = Column(
        Boolean,
        nullable=False,
        comment="신고와 함께 차단 여부",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="신고 생성 시간",
    )

    # 관계 설정
    reporter = relationship("User", foreign_keys=[reporter_id], backref="reports_made")
    reported_user = relationship(
        "User", foreign_keys=[reported_user_id], backref="reports_received"
    )
