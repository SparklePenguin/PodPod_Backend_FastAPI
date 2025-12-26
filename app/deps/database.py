"""Database dependency injection functions"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션을 관리하는 의존성 함수"""
    logger.debug("Creating new database session")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            logger.debug("Committing transaction")
            await session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Rolling back transaction due to SQLAlchemyError: {e}")
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Rolling back transaction due to Exception: {e}")
            await session.rollback()
            raise
        finally:
            logger.debug("Closing database session")
