"""Follow Feature Containers"""

from dependency_injector import containers, providers

from app.core.containers.core_container import CoreContainer
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.follow.use_cases.follow_use_case import FollowUseCase


# MARK: - Repository Containers
class FollowRepoContainer(containers.DeclarativeContainer):
    """팔로우 Repository 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    follow_repo = providers.Factory(FollowRepository, session=core.session)


# MARK: - UseCase Containers
class FollowUseCaseContainer(containers.DeclarativeContainer):
    """팔로우 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    follow_use_case = providers.Factory(
        FollowUseCase,
        session=core.session,
        fcm_service=core.fcm_service,
    )


# MARK: - Aggregate Container
class FollowContainer(containers.DeclarativeContainer):
    """팔로우 통합 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    # Repositories
    repo: FollowRepoContainer = providers.Container(FollowRepoContainer, core=core)

    # UseCases
    use_case: FollowUseCaseContainer = providers.Container(FollowUseCaseContainer, core=core)
