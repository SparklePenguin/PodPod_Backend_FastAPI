"""Notification Feature Containers"""

from dependency_injector import containers, providers


# MARK: - Repository Containers
class NotificationRepoContainer(containers.DeclarativeContainer):
    """알림 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.notifications.repositories.notification_repository import (
        NotificationRepository,
    )

    core: CoreContainer = providers.DependenciesContainer()

    notification_repo = providers.Factory(NotificationRepository, session=core.session)


# MARK: - Service Containers
class NotificationDtoServiceContainer(containers.DeclarativeContainer):
    """알림 DTO Service 컨테이너"""

    from app.core.containers.tendency_container import TendencyRepoContainer
    from app.features.notifications.services.notification_dto_service import (
        NotificationDtoService,
    )

    tendency_repo: TendencyRepoContainer = providers.DependenciesContainer()

    notification_dto_service = providers.Factory(
        NotificationDtoService,
        tendency_repo=tendency_repo.tendency_repo,
    )


# MARK: - UseCase Containers
class NotificationUseCaseContainer(containers.DeclarativeContainer):
    """알림 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.tendency_container import TendencyRepoContainer
    from app.features.notifications.use_cases.notification_use_case import (
        NotificationUseCase,
    )

    core: CoreContainer = providers.DependenciesContainer()
    notification_repo: NotificationRepoContainer = providers.DependenciesContainer()
    tendency_repo: TendencyRepoContainer = providers.DependenciesContainer()
    dto_service: NotificationDtoServiceContainer = providers.DependenciesContainer()

    notification_use_case = providers.Factory(
        NotificationUseCase,
        session=core.session,
        notification_repo=notification_repo.notification_repo,
        tendency_repo=tendency_repo.tendency_repo,
        dto_service=dto_service.notification_dto_service,
    )


# MARK: - Aggregate Container
class NotificationContainer(containers.DeclarativeContainer):
    """알림 통합 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.tendency_container import TendencyRepoContainer
    from app.features.notifications.repositories.notification_repository import (
        NotificationRepository,
    )
    from app.features.notifications.services.notification_dto_service import (
        NotificationDtoService,
    )
    from app.features.notifications.use_cases.notification_use_case import (
        NotificationUseCase,
    )

    core: CoreContainer = providers.DependenciesContainer()

    # TendencyRepoContainer를 직접 생성
    tendency_repo: TendencyRepoContainer = providers.Container(
        TendencyRepoContainer, core=core
    )

    # Repositories
    repo: NotificationRepoContainer = providers.Container(
        NotificationRepoContainer, core=core
    )

    # Services
    service: NotificationDtoServiceContainer = providers.Container(
        NotificationDtoServiceContainer,
        tendency_repo=tendency_repo,
    )

    # UseCases
    use_case: NotificationUseCaseContainer = providers.Container(
        NotificationUseCaseContainer,
        core=core,
        notification_repo=repo,
        tendency_repo=tendency_repo,
        dto_service=service,
    )

    # 편의를 위한 alias
    notification_repo: providers.Factory[NotificationRepository] = repo.notification_repo
    notification_dto_service: providers.Factory[NotificationDtoService] = (
        service.notification_dto_service
    )
    notification_use_case: providers.Factory[NotificationUseCase] = (
        use_case.notification_use_case
    )
