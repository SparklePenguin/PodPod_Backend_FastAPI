from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String

from app.core.database import Base


class TendencyResult(Base):
    """성향 테스트 결과 모델"""

    __tablename__ = "tendency_results"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(
        String(50), nullable=False, unique=True
    )  # quietMate, togetherMate, fieldMate, supportMate
    description = Column(String(200), nullable=False)

    # JSON 형태로 저장할 상세 정보
    tendency_info = Column(
        JSON, nullable=False
    )  # mainType, subType, speechBubbles, oneLineDescriptions, detailedDescription, keywords

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
