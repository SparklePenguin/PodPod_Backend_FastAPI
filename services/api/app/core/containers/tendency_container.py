"""Tendency Feature Containers"""

from dependency_injector import containers, providers

from app.core.containers.core_container import CoreContainer
from app.features.tendencies.repositories.tendency_repository import (
    TendencyRepository,
)
from app.features.tendencies.services.tendency_calculation_service import (
    TendencyCalculationService,
)
from app.features.tendencies.use_cases.tendency_use_case import TendencyUseCase


# MARK: - Repository Containers
class TendencyRepoContainer(containers.DeclarativeContainer):
    """성향 Repository 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    tendency_repo = providers.Factory(TendencyRepository, session=core.session)


# MARK: - Service Containers
class TendencyCalculationServiceContainer(containers.DeclarativeContainer):
    """성향 계산 Service 컨테이너"""

    tendency_calculation_service = providers.Singleton(TendencyCalculationService)


# MARK: - UseCase Containers
class TendencyUseCaseContainer(containers.DeclarativeContainer):
    """성향 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()
    tendency_repo: TendencyRepoContainer = providers.DependenciesContainer()
    calculation_service: TendencyCalculationServiceContainer = providers.DependenciesContainer()

    tendency_use_case = providers.Factory(
        TendencyUseCase,
        session=core.session,
        tendency_repo=tendency_repo.tendency_repo,
        calculation_service=calculation_service.tendency_calculation_service,
    )


# MARK: - Aggregate Container
class TendencyContainer(containers.DeclarativeContainer):
    """성향 통합 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    # Repositories
    repo: TendencyRepoContainer = providers.Container(TendencyRepoContainer, core=core)

    # Services
    service: TendencyCalculationServiceContainer = providers.Container(
        TendencyCalculationServiceContainer
    )

    # UseCases
    use_case: TendencyUseCaseContainer = providers.Container(
        TendencyUseCaseContainer,
        core=core,
        tendency_repo=repo,
        calculation_service=service,
    )
