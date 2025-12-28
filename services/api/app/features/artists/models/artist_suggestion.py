from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.core.database import Base


class ArtistSuggestion(Base):
    """아티스트 제안 모델"""

    __tablename__ = "artist_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    artist_name = Column(String(100), nullable=False, index=True, comment="아티스트명")
    reason = Column(Text, nullable=True, comment="추천 이유")
    email = Column(String(255), nullable=True, comment="이메일 주소")
    user_id = Column(Integer, nullable=True, index=True, comment="제안한 사용자 ID")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="생성일시"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="수정일시",
    )

    def __repr__(self):
        return f"<ArtistSuggestion(id={self.id}, artist_name='{self.artist_name}', email='{self.email}')>"
