from fastapi import FastAPI
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.api import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization error: {e}")
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
    ],
)

# 보안 스키마 정의
security = HTTPBearer()

# API 라우터 포함
app.include_router(api_router, prefix="/api/v1")
