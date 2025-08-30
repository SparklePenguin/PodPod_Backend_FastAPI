from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.api import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.exceptions import (
    validation_exception_handler,
    pydantic_validation_exception_handler,
    general_exception_handler,
)
import logging

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="소셜 로그인을 지원하는 FastAPI 백엔드",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "users",
            "description": "사용자 관리 API",
        },
        {
            "name": "sessions",
            "description": "세션 관리 API (로그인/로그아웃)",
        },
        {
            "name": "artists",
            "description": "아티스트 관리 API",
        },
        {
            "name": "oauths",
            "description": "OAuth 인증 API",
        },
        {
            "name": "internal",
            "description": "⚠️ 내부용 API - 개발/테스트 목적으로만 사용됩니다.",
        },
    ],
)

# 보안 스키마 정의
security = HTTPBearer()

# 예외 핸들러 등록
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# API 라우터 포함
app.include_router(api_router, prefix="/api/v1")
