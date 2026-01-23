import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from app.features.oauth.routers import OAuthController
from settings.openapi_tags import API_TAGS

# 프로젝트 루트를 Python 경로에 추가 (shared 모듈 import를 위해)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.v1.router import api_router, UserCommonController  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import init_db  # noqa: E402
from app.core.exceptions import (  # noqa: E402
    register_exception_handlers,
    BusinessException,
    business_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    value_error_handler,
)
from app.core.logger import setup_logging  # noqa: E402
from app.core.startup import startup_events, sync_startup_events  # noqa: E402
from app.middleware.logging_middleware import LoggingMiddleware  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.security import HTTPBearer  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from prometheus_fastapi_instrumentator import Instrumentator  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402

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
    title=settings.app.name,
    version=settings.app.version,
    description=settings.app.description,
    lifespan=lifespan,
    root_path=settings.app.root_path if hasattr(settings, "ROOT_PATH") else "",
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
app.openapi_tags = API_TAGS

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
# 환경별 uploads 디렉토리 사용 (config.py에서 설정됨)
UPLOADS_DIR = settings.UPLOADS_DIR
BASE_DIR = Path(__file__).resolve().parent

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")

# API 라우터 포함
app.include_router(api_router, prefix="/api/v1")
