"""Core Infrastructure Container"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from app.core.config import settings

if TYPE_CHECKING:
    from app.features.chat.services.websocket_service import WebSocketService


def _create_websocket_service() -> WebSocketService | None:
    """WebSocketService를 조건부로 생성하는 헬퍼 함수"""
    if settings.USE_WEBSOCKET_CHAT:
        from app.features.chat.services.websocket_service import WebSocketService

        return WebSocketService()
    return None


class CoreContainer(containers.DeclarativeContainer):
    """핵심 인프라 의존성 컨테이너"""

    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession

    # MARK: - Configuration
    config = providers.Configuration()

    # MARK: - External Dependencies
    session = providers.Dependency(instance_of=AsyncSession)
    redis = providers.Dependency(instance_of=Redis)

    # MARK: - Services
    from app.features.notifications.services.fcm_service import FCMService
    from app.features.users.services.random_profile_image_service import (
        RandomProfileImageService,
    )

    fcm_service = providers.Singleton(FCMService)
    random_profile_image_service = providers.Singleton(RandomProfileImageService)

    websocket_service = providers.Singleton(_create_websocket_service)
