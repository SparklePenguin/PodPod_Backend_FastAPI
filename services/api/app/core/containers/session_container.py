"""Session Feature Containers"""

from dependency_injector import containers, providers

from app.core.containers.core_container import CoreContainer
from app.features.session.repositories.session_repository import SessionRepository
from app.features.session.use_cases.session_use_case import SessionUseCase


# MARK: - Repository Containers
class SessionRepoContainer(containers.DeclarativeContainer):
    """세션 Repository 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    session_repo = providers.Factory(SessionRepository, session=core.session)


# MARK: - UseCase Containers
class SessionUseCaseContainer(containers.DeclarativeContainer):
    """세션 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()
    session_repo: SessionRepoContainer = providers.DependenciesContainer()

    session_use_case = providers.Factory(
        SessionUseCase,
        session=core.session,
        session_repo=session_repo.session_repo,
    )


# MARK: - Aggregate Container
class SessionContainer(containers.DeclarativeContainer):
    """세션 통합 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    # Repositories
    repo: SessionRepoContainer = providers.Container(SessionRepoContainer, core=core)

    # UseCases
    use_case: SessionUseCaseContainer = providers.Container(
        SessionUseCaseContainer, core=core, session_repo=repo
    )
