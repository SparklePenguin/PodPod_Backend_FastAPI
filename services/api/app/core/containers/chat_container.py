"""Chat Feature Containers"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

if TYPE_CHECKING:
    from app.features.chat.services.websocket_service import (
        ConnectionManager,
        WebSocketService,
    )


def _get_connection_manager(ws: WebSocketService | None) -> ConnectionManager | None:
    """WebSocketService에서 ConnectionManager를 추출하는 헬퍼 함수"""
    return ws.get_connection_manager() if ws else None


# MARK: - Repository Containers
class ChatRepoContainer(containers.DeclarativeContainer):
    """채팅 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.chat.repositories.chat_repository import ChatRepository

    core: CoreContainer = providers.DependenciesContainer()

    chat_repo = providers.Factory(ChatRepository, session=core.session)


class ChatRoomRepoContainer(containers.DeclarativeContainer):
    """채팅방 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.chat.repositories.chat_room_repository import ChatRoomRepository

    core: CoreContainer = providers.DependenciesContainer()

    chat_room_repo = providers.Factory(ChatRoomRepository, session=core.session)


class ChatUserRepoContainer(containers.DeclarativeContainer):
    """채팅용 사용자 Repository 컨테이너 (순환 참조 방지)"""

    from app.core.containers.core_container import CoreContainer
    from app.features.users.repositories import UserRepository

    core: CoreContainer = providers.DependenciesContainer()

    user_repo = providers.Factory(UserRepository, session=core.session)


class ChatPodRepoContainer(containers.DeclarativeContainer):
    """채팅용 파티 Repository 컨테이너 (순환 참조 방지)"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.repositories.pod_repository import PodRepository

    core: CoreContainer = providers.DependenciesContainer()

    pod_repo = providers.Factory(PodRepository, session=core.session)


# MARK: - Service Containers
class ChatMessageServiceContainer(containers.DeclarativeContainer):
    """채팅 메시지 Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.chat.services.chat_message_service import ChatMessageService

    core: CoreContainer = providers.DependenciesContainer()
    chat_repo: ChatRepoContainer = providers.DependenciesContainer()
    user_repo: ChatUserRepoContainer = providers.DependenciesContainer()

    chat_message_service = providers.Factory(
        ChatMessageService,
        chat_repo=chat_repo.chat_repo,
        user_repo=user_repo.user_repo,
        redis=core.redis,
    )


class ChatPodServiceContainer(containers.DeclarativeContainer):
    """채팅 파티 Service 컨테이너"""

    from app.features.chat.services.chat_pod_service import ChatPodService

    pod_repo: ChatPodRepoContainer = providers.DependenciesContainer()

    chat_pod_service = providers.Factory(
        ChatPodService,
        pod_repo=pod_repo.pod_repo,
    )


class ChatNotificationServiceContainer(containers.DeclarativeContainer):
    """채팅 알림 Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.chat.services.chat_notification_service import (
        ChatNotificationService,
    )

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: ChatUserRepoContainer = providers.DependenciesContainer()
    chat_room_repo: ChatRoomRepoContainer = providers.DependenciesContainer()

    chat_notification_service = providers.Factory(
        ChatNotificationService,
        session=core.session,
        user_repo=user_repo.user_repo,
        chat_room_repo=chat_room_repo.chat_room_repo,
        fcm_service=core.fcm_service,
        redis=core.redis,
        connection_manager=providers.Callable(
            _get_connection_manager,
            core.websocket_service,
        ),
    )


# MARK: - UseCase Containers
class ChatRoomUseCaseContainer(containers.DeclarativeContainer):
    """채팅방 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.chat.use_cases.chat_room_use_case import ChatRoomUseCase

    core: CoreContainer = providers.DependenciesContainer()
    chat_room_repo: ChatRoomRepoContainer = providers.DependenciesContainer()
    chat_repo: ChatRepoContainer = providers.DependenciesContainer()

    chat_room_use_case = providers.Factory(
        ChatRoomUseCase,
        session=core.session,
        chat_room_repo=chat_room_repo.chat_room_repo,
        chat_repo=chat_repo.chat_repo,
        redis=core.redis,
    )


class ChatUseCaseContainer(containers.DeclarativeContainer):
    """채팅 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.chat.use_cases.chat_use_case import ChatUseCase

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: ChatUserRepoContainer = providers.DependenciesContainer()
    chat_room_repo: ChatRoomRepoContainer = providers.DependenciesContainer()
    message_service: ChatMessageServiceContainer = providers.DependenciesContainer()
    pod_service: ChatPodServiceContainer = providers.DependenciesContainer()
    notification_service: ChatNotificationServiceContainer = providers.DependenciesContainer()

    chat_use_case = providers.Factory(
        ChatUseCase,
        session=core.session,
        user_repo=user_repo.user_repo,
        chat_room_repo=chat_room_repo.chat_room_repo,
        message_service=message_service.chat_message_service,
        pod_service=pod_service.chat_pod_service,
        notification_service=notification_service.chat_notification_service,
        websocket_service=core.websocket_service,
    )


# MARK: - Aggregate Container
class ChatContainer(containers.DeclarativeContainer):
    """채팅 통합 컨테이너"""

    from app.core.containers.core_container import CoreContainer

    core: CoreContainer = providers.DependenciesContainer()

    # Repositories
    chat_repo: ChatRepoContainer = providers.Container(ChatRepoContainer, core=core)
    chat_room_repo: ChatRoomRepoContainer = providers.Container(
        ChatRoomRepoContainer, core=core
    )
    user_repo: ChatUserRepoContainer = providers.Container(ChatUserRepoContainer, core=core)
    pod_repo: ChatPodRepoContainer = providers.Container(ChatPodRepoContainer, core=core)

    # Services
    chat_message_service: ChatMessageServiceContainer = providers.Container(
        ChatMessageServiceContainer,
        core=core,
        chat_repo=chat_repo,
        user_repo=user_repo,
    )
    chat_pod_service: ChatPodServiceContainer = providers.Container(
        ChatPodServiceContainer,
        pod_repo=pod_repo,
    )
    chat_notification_service: ChatNotificationServiceContainer = providers.Container(
        ChatNotificationServiceContainer,
        core=core,
        user_repo=user_repo,
        chat_room_repo=chat_room_repo,
    )

    # UseCases
    chat_room_use_case: ChatRoomUseCaseContainer = providers.Container(
        ChatRoomUseCaseContainer,
        core=core,
        chat_room_repo=chat_room_repo,
        chat_repo=chat_repo,
    )
    chat_use_case: ChatUseCaseContainer = providers.Container(
        ChatUseCaseContainer,
        core=core,
        user_repo=user_repo,
        chat_room_repo=chat_room_repo,
        message_service=chat_message_service,
        pod_service=chat_pod_service,
        notification_service=chat_notification_service,
    )
