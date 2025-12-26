"""
Scraping Service - 아티스트 이미지 생성 및 MVP 동기화
"""
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가 (메인 API의 app 모듈 접근용)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db

from app.routers import artist_router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="PodPod Scraping Service",
    version="1.0.0",
    description="아티스트 이미지 생성 및 MVP 동기화 서비스",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(artist_router.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("🚀 Scraping Service Starting...")
    await init_db()
    logger.info("✅ Database initialized")


@app.get("/")
async def root():
    """헬스체크"""
    return {
        "service": "PodPod Scraping Service",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}
