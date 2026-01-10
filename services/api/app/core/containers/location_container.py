"""Location Feature Containers"""

from dependency_injector import containers, providers


# ===================
# UseCase Containers
# ===================
class LocationUseCaseContainer(containers.DeclarativeContainer):
    """위치 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.locations.use_cases.location_use_case import LocationUseCase

    core: CoreContainer = providers.DependenciesContainer()

    location_use_case = providers.Factory(LocationUseCase, session=core.session)


# ===================
# Aggregate Container
# ===================
class LocationContainer(containers.DeclarativeContainer):
    """위치 통합 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.locations.use_cases.location_use_case import LocationUseCase

    core: CoreContainer = providers.DependenciesContainer()

    # UseCases
    use_case: LocationUseCaseContainer = providers.Container(
        LocationUseCaseContainer, core=core
    )

    # 편의를 위한 alias
    location_use_case: providers.Factory[LocationUseCase] = use_case.location_use_case
