from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base
from app.models.user_state import UserState


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
        Enum(UserState), default=UserState.PREFERRED_ARTISTS
    )  # 사용자 온보딩 상태
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    # 소셜 로그인 관련 필드
    auth_provider = Column(String(20), nullable=True)  # 'kakao', 'google', 'apple'
    auth_provider_id = Column(
        String(100), unique=True, index=True, nullable=True
    )  # 소셜 제공자의 고유 ID

    # FCM 토큰 (푸시 알림용)
    fcm_token = Column(String(500), nullable=True)  # Firebase Cloud Messaging 토큰

    # 관계 설정
    preferred_artists = relationship("PreferredArtist", back_populates="user")

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
