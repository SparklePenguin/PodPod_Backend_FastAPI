import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings

# 로거 설정
logger = logging.getLogger(__name__)

# 비동기 엔진 생성 (개발 환경에서만 SQL 로그 출력)
engine = create_async_engine(settings.DATABASE_URL, echo=False)  # SQL 로그 비활성화

# 세션 팩토리 생성 (비동기용)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base 클래스 생성
Base = declarative_base()


# 데이터베이스 세션 의존성
async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 데이터베이스 초기화 (개발 환경에서만 테이블 생성)
async def init_db():
    # 개발 환경에서만 테이블 자동 생성
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
