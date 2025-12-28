from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String

from app.core.database import Base


class UserTendencyResult(Base):
    """사용자 성향 테스트 결과 모델"""

    __tablename__ = "user_tendency_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tendency_type = Column(
        String(50), nullable=False
    )  # quietMate, togetherMate, fieldMate, supportMate

    # 테스트 응답 데이터 (JSON)
    answers = Column(JSON, nullable=False)  # 사용자의 답변 데이터

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
