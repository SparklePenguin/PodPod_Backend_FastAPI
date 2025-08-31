from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


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
    needs_onboarding = Column(Boolean, default=True)
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

    # 관계 설정
    preferred_artists = relationship("PreferredArtist", back_populates="user")
