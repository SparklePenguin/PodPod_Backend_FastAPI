import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import (
    BusinessException,
    business_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    value_error_handler,
)
from app.core.exception_loader import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.startup import startup_events, sync_startup_events
from app.middleware.logging_middleware import LoggingMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # 동기 시작 이벤트
        sync_startup_events()

        # 비동기 시작 이벤트
        await startup_events()

        # 데이터베이스 초기화
        await init_db()
        logger.info("Database initialized successfully!")

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="소셜 로그인을 지원하는 FastAPI 백엔드",
    lifespan=lifespan,
    root_path=settings.ROOT_PATH if hasattr(settings, "ROOT_PATH") else "",
)

# Prometheus 메트릭 수집 설정
Instrumentator().instrument(app).expose(app)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 개발 서버
        "http://localhost:3001",  # 추가 React 포트
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8000",  # FastAPI 자체
        "http://127.0.0.1:8000",
        "*",  # 개발 환경에서는 모든 origin 허용
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
)

# 로깅 미들웨어 추가
app.add_middleware(LoggingMiddleware)

# OpenAPI 태그 설정
app.openapi_tags = [
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
    {
        "name": "profile-images",
        "description": "랜덤 프로필 이미지 API",
    },
]

# 보안 스키마 정의
security = HTTPBearer()

# 예외 핸들러 등록
# 타입 체커를 위한 타입 캐스팅
app.add_exception_handler(HTTPException, cast(Any, http_exception_handler))  # type: ignore
app.add_exception_handler(
    StarletteHTTPException,
    cast(Any, http_exception_handler),  # type: ignore
)  # Starlette의 405 등 처리
app.add_exception_handler(
    RequestValidationError, cast(Any, validation_exception_handler)
)  # type: ignore
app.add_exception_handler(ValueError, cast(Any, value_error_handler))  # type: ignore
app.add_exception_handler(BusinessException, cast(Any, business_exception_handler))  # type: ignore
app.add_exception_handler(Exception, cast(Any, general_exception_handler))  # type: ignore

# 도메인별 예외 핸들러 자동 등록
register_exception_handlers(app)

# 정적 파일 서빙 설정
# main.py 기준 절대 경로 사용 (프로젝트 루트에서 uvicorn 실행 시에도 동작)
BASE_DIR = Path(__file__).resolve().parent

# uploads 디렉토리가 없으면 생성
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")

# API 라우터 포함
app.include_router(api_router, prefix="/api/v1")
