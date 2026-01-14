"""Artist Feature Containers"""

from dependency_injector import containers, providers

from app.core.containers.core_container import CoreContainer
from app.features.artists.repositories.artist_repository import ArtistRepository
from app.features.artists.use_cases.artist_schedule_use_cases import (
    GetScheduleByIdUseCase,
    GetSchedulesUseCase,
)
from app.features.artists.use_cases.artist_suggestion_use_cases import (
    CreateArtistSuggestionUseCase,
    GetArtistRankingUseCase,
    GetSuggestionByIdUseCase,
    GetSuggestionsByArtistNameUseCase,
    GetSuggestionsUseCase,
)
from app.features.artists.use_cases.artist_use_cases import (
    GetArtistUseCase,
    GetArtistsUseCase,
)


# MARK: - Repository Containers
class ArtistRepoContainer(containers.DeclarativeContainer):
    """아티스트 Repository 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    artist_repo = providers.Factory(ArtistRepository, session=core.session)


# MARK: - UseCase Containers
class GetArtistUseCaseContainer(containers.DeclarativeContainer):
    """아티스트 조회 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    get_artist_use_case = providers.Factory(GetArtistUseCase, session=core.session)


class GetArtistsUseCaseContainer(containers.DeclarativeContainer):
    """아티스트 목록 조회 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    get_artists_use_case = providers.Factory(GetArtistsUseCase, session=core.session)


class GetScheduleByIdUseCaseContainer(containers.DeclarativeContainer):
    """스케줄 단일 조회 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    get_schedule_by_id_use_case = providers.Factory(GetScheduleByIdUseCase, session=core.session)


class GetSchedulesUseCaseContainer(containers.DeclarativeContainer):
    """스케줄 목록 조회 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    get_schedules_use_case = providers.Factory(GetSchedulesUseCase, session=core.session)


class CreateArtistSuggestionUseCaseContainer(containers.DeclarativeContainer):
    """아티스트 건의 생성 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    create_artist_suggestion_use_case = providers.Factory(
        CreateArtistSuggestionUseCase, session=core.session
    )


class GetSuggestionByIdUseCaseContainer(containers.DeclarativeContainer):
    """건의 단일 조회 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    get_suggestion_by_id_use_case = providers.Factory(
        GetSuggestionByIdUseCase, session=core.session
    )


class GetSuggestionsUseCaseContainer(containers.DeclarativeContainer):
    """건의 목록 조회 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    get_suggestions_use_case = providers.Factory(GetSuggestionsUseCase, session=core.session)


class GetArtistRankingUseCaseContainer(containers.DeclarativeContainer):
    """아티스트 랭킹 조회 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    get_artist_ranking_use_case = providers.Factory(
        GetArtistRankingUseCase, session=core.session
    )


class GetSuggestionsByArtistNameUseCaseContainer(containers.DeclarativeContainer):
    """아티스트 이름별 건의 조회 UseCase 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    get_suggestions_by_artist_name_use_case = providers.Factory(
        GetSuggestionsByArtistNameUseCase, session=core.session
    )


# MARK: - Aggregate Container
class ArtistContainer(containers.DeclarativeContainer):
    """아티스트 통합 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    # Repositories
    repo: ArtistRepoContainer = providers.Container(ArtistRepoContainer, core=core)

    # UseCases
    get_artist_use_case: GetArtistUseCaseContainer = providers.Container(
        GetArtistUseCaseContainer, core=core
    )
    get_artists_use_case: GetArtistsUseCaseContainer = providers.Container(
        GetArtistsUseCaseContainer, core=core
    )
    get_schedule_by_id_use_case: GetScheduleByIdUseCaseContainer = providers.Container(
        GetScheduleByIdUseCaseContainer, core=core
    )
    get_schedules_use_case: GetSchedulesUseCaseContainer = providers.Container(
        GetSchedulesUseCaseContainer, core=core
    )
    create_artist_suggestion_use_case: CreateArtistSuggestionUseCaseContainer = providers.Container(
        CreateArtistSuggestionUseCaseContainer, core=core
    )
    get_suggestion_by_id_use_case: GetSuggestionByIdUseCaseContainer = providers.Container(
        GetSuggestionByIdUseCaseContainer, core=core
    )
    get_suggestions_use_case: GetSuggestionsUseCaseContainer = providers.Container(
        GetSuggestionsUseCaseContainer, core=core
    )
    get_artist_ranking_use_case: GetArtistRankingUseCaseContainer = providers.Container(
        GetArtistRankingUseCaseContainer, core=core
    )
    get_suggestions_by_artist_name_use_case: GetSuggestionsByArtistNameUseCaseContainer = (
        providers.Container(GetSuggestionsByArtistNameUseCaseContainer, core=core)
    )
