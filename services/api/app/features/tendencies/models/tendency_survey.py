from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String

from app.core.database import Base


class TendencySurvey(Base):
    """성향 테스트 설문 모델"""

    __tablename__ = "tendency_surveys"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)

    # JSON 형태로 저장할 설문 데이터
    survey_data = Column(JSON, nullable=False)  # questions 배열

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
