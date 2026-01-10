"""
Health Check Router
시스템 상태 확인 엔드포인트
"""

from datetime import datetime, timezone

from app.common.schemas import BaseResponse
from app.core.database import get_session
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["health"])


class HealthCheckDto(BaseModel):
    """서버 상태 응답"""

    status: str = Field(description="서버 상태")
    timestamp: str = Field(description="확인 시간")
    database: str = Field(description="데이터베이스 상태")
    version: str = Field(description="API 버전")

    model_config = {"populate_by_name": True}


# - MARK: 서버 상태 확인
@router.get(
    "/health",
    response_model=BaseResponse[HealthCheckDto],
    description="서버 & 데이터베이스 연결 상태 확인",
)
async def health_check(db: AsyncSession = Depends(get_session)):
    """서버 상태 확인 (Health Check)"""

    # 데이터베이스 연결 확인
    db_status = "disconnected"
    try:
        # 간단한 쿼리로 DB 연결 확인
        result = await db.execute(text("SELECT 1"))
        if result:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 버전 정보 가져오기
    from app.core.config import settings

    health_data = HealthCheckDto(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        version=settings.APP_VERSION,
    )

    return BaseResponse.ok(
        data=health_data,
        message_ko="서버가 정상 작동 중입니다.",
        message_en="Server is running healthy.",
    )


# - MARK: 서버 Ping
@router.get(
    "/ping",
    description="서버 확인 (DB 체크 없음)",
)
async def ping():
    """서버 Ping (DB 체크 없이 빠른 응답)"""
    return {"status": "ok", "message": "pong"}
