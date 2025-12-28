"""
Health Check Router
시스템 상태 확인 엔드포인트
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse
from app.core.database import get_session
from app.core.http_status import HttpStatus

router = APIRouter()


class HealthCheckResponse(BaseModel):
    """서버 상태 응답"""

    status: str = Field(serialization_alias="status", description="서버 상태")
    timestamp: str = Field(serialization_alias="timestamp", description="확인 시간")
    database: str = Field(
        serialization_alias="database", description="데이터베이스 상태"
    )
    version: str = Field(serialization_alias="version", description="API 버전")

    model_config = {"populate_by_name": True}


@router.get(
    "/health",
    response_model=BaseResponse[HealthCheckResponse],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[HealthCheckResponse],
            "description": "서버 정상 작동",
        },
    },
    summary="서버 상태 확인",
    description="서버와 데이터베이스 연결 상태를 확인합니다.",
    tags=["health"],
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

    health_data = HealthCheckResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        database=db_status,
        version=settings.APP_VERSION,
    )

    return BaseResponse.ok(
        data=health_data,
        message_ko="서버가 정상 작동 중입니다.",
        message_en="Server is running healthy.",
    )


@router.get(
    "/ping",
    summary="서버 Ping",
    description="서버가 살아있는지 간단히 확인합니다 (DB 체크 없음).",
    tags=["health"],
)
async def ping():
    """서버 Ping (DB 체크 없이 빠른 응답)"""
    return {"status": "ok", "message": "pong"}
