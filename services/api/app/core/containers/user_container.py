"""User Feature Containers"""

from dependency_injector import containers, providers


# ===================
# Repository Containers
# ===================
class UserRepoContainer(containers.DeclarativeContainer):
    """사용자 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.users.repositories import UserRepository

    core: CoreContainer = providers.DependenciesContainer()

    user_repo = providers.Factory(UserRepository, session=core.session)


class UserArtistRepoContainer(containers.DeclarativeContainer):
    """사용자-아티스트 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.users.repositories.user_artist_repository import (
        UserArtistRepository,
    )

    core: CoreContainer = providers.DependenciesContainer()

    user_artist_repo = providers.Factory(UserArtistRepository, session=core.session)


class BlockUserRepoContainer(containers.DeclarativeContainer):
    """차단 사용자 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.users.repositories import BlockUserRepository

    core: CoreContainer = providers.DependenciesContainer()

    block_user_repo = providers.Factory(BlockUserRepository, session=core.session)


class UserNotificationRepoContainer(containers.DeclarativeContainer):
    """사용자 알림 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.users.repositories import UserNotificationRepository

    core: CoreContainer = providers.DependenciesContainer()

    user_notification_repo = providers.Factory(UserNotificationRepository, session=core.session)


class UserReportRepoContainer(containers.DeclarativeContainer):
    """사용자 신고 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.users.repositories import UserReportRepository

    core: CoreContainer = providers.DependenciesContainer()

    user_report_repo = providers.Factory(UserReportRepository, session=core.session)


# ===================
# Service Containers
# ===================
class UserDtoServiceContainer(containers.DeclarativeContainer):
    """사용자 DTO Service 컨테이너"""

    from app.features.users.services.user_dto_service import UserDtoService

    user_dto_service = providers.Singleton(UserDtoService)


class UserStateServiceContainer(containers.DeclarativeContainer):
    """사용자 상태 Service 컨테이너"""

    from app.features.users.services.user_state_service import UserStateService

    user_state_service = providers.Singleton(UserStateService)


# ===================
# UseCase Containers
# ===================
class UserUseCaseContainer(containers.DeclarativeContainer):
    """사용자 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import (
        FollowRepoContainer,
        FollowUseCaseContainer,
    )
    from app.core.containers.notification_container import NotificationRepoContainer
    from app.core.containers.pod_container import PodRepoContainer
    from app.core.containers.tendency_container import TendencyRepoContainer
    from app.features.users.use_cases.user_use_case import UserUseCase

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: UserRepoContainer = providers.DependenciesContainer()
    user_artist_repo: UserArtistRepoContainer = providers.DependenciesContainer()
    user_notification_repo: UserNotificationRepoContainer = providers.DependenciesContainer()
    follow_repo: FollowRepoContainer = providers.DependenciesContainer()
    follow_use_case: FollowUseCaseContainer = providers.DependenciesContainer()
    notification_repo: NotificationRepoContainer = providers.DependenciesContainer()
    tendency_repo: TendencyRepoContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    user_state_service: UserStateServiceContainer = providers.DependenciesContainer()
    user_dto_service: UserDtoServiceContainer = providers.DependenciesContainer()

    user_use_case = providers.Factory(
        UserUseCase,
        session=core.session,
        user_repo=user_repo.user_repo,
        user_artist_repo=user_artist_repo.user_artist_repo,
        follow_use_case=follow_use_case.follow_use_case,
        follow_repo=follow_repo.follow_repo,
        pod_application_repo=pod_repo.application_repo,
        pod_repo=pod_repo.pod_repo,
        pod_like_repo=pod_repo.pod_like_repo,
        notification_repo=notification_repo.notification_repo,
        user_notification_repo=user_notification_repo.user_notification_repo,
        tendency_repo=tendency_repo.tendency_repo,
        user_state_service=user_state_service.user_state_service,
        user_dto_service=user_dto_service.user_dto_service,
    )


class BlockUserUseCaseContainer(containers.DeclarativeContainer):
    """차단 사용자 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowRepoContainer
    from app.core.containers.tendency_container import TendencyRepoContainer
    from app.features.users.use_cases.block_user_use_case import BlockUserUseCase

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: UserRepoContainer = providers.DependenciesContainer()
    block_user_repo: BlockUserRepoContainer = providers.DependenciesContainer()
    follow_repo: FollowRepoContainer = providers.DependenciesContainer()
    tendency_repo: TendencyRepoContainer = providers.DependenciesContainer()

    block_user_use_case = providers.Factory(
        BlockUserUseCase,
        session=core.session,
        block_repo=block_user_repo.block_user_repo,
        user_repo=user_repo.user_repo,
        follow_repo=follow_repo.follow_repo,
        tendency_repo=tendency_repo.tendency_repo,
    )


class UserNotificationUseCaseContainer(containers.DeclarativeContainer):
    """사용자 알림 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.notification_container import (
        NotificationDtoServiceContainer,
    )
    from app.features.users.use_cases.user_notification_use_case import (
        UserNotificationUseCase,
    )

    core: CoreContainer = providers.DependenciesContainer()
    user_notification_repo: UserNotificationRepoContainer = providers.DependenciesContainer()
    notification_service: NotificationDtoServiceContainer = providers.DependenciesContainer()

    user_notification_use_case = providers.Factory(
        UserNotificationUseCase,
        session=core.session,
        notification_repo=user_notification_repo.user_notification_repo,
        notification_dto_service=notification_service.notification_dto_service,
    )


class UserArtistUseCaseContainer(containers.DeclarativeContainer):
    """사용자-아티스트 UseCase 컨테이너"""

    from app.core.containers.artist_container import ArtistRepoContainer
    from app.core.containers.core_container import CoreContainer
    from app.features.users.use_cases.user_artist_use_case import UserArtistUseCase

    core: CoreContainer = providers.DependenciesContainer()
    user_artist_repo: UserArtistRepoContainer = providers.DependenciesContainer()
    artist_repo: ArtistRepoContainer = providers.DependenciesContainer()

    user_artist_use_case = providers.Factory(
        UserArtistUseCase,
        session=core.session,
        user_artist_repo=user_artist_repo.user_artist_repo,
        artist_repo=artist_repo.artist_repo,
    )


# ===================
# Aggregate Container
# ===================
class UserContainer(containers.DeclarativeContainer):
    """사용자 통합 컨테이너"""

    from app.core.containers.artist_container import ArtistContainer
    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowContainer
    from app.core.containers.notification_container import NotificationContainer
    from app.core.containers.pod_container import PodContainer
    from app.core.containers.tendency_container import TendencyContainer

    core: CoreContainer = providers.DependenciesContainer()
    follow: FollowContainer = providers.DependenciesContainer()
    notification: NotificationContainer = providers.DependenciesContainer()
    tendency: TendencyContainer = providers.DependenciesContainer()
    pod: PodContainer = providers.DependenciesContainer()
    artist: ArtistContainer = providers.DependenciesContainer()

    # Repositories
    user_repo: UserRepoContainer = providers.Container(UserRepoContainer, core=core)
    user_artist_repo: UserArtistRepoContainer = providers.Container(
        UserArtistRepoContainer, core=core
    )
    block_user_repo: BlockUserRepoContainer = providers.Container(
        BlockUserRepoContainer, core=core
    )
    user_notification_repo: UserNotificationRepoContainer = providers.Container(
        UserNotificationRepoContainer, core=core
    )
    user_report_repo: UserReportRepoContainer = providers.Container(
        UserReportRepoContainer, core=core
    )

    # Services
    user_dto_service: UserDtoServiceContainer = providers.Container(UserDtoServiceContainer)
    user_state_service: UserStateServiceContainer = providers.Container(
        UserStateServiceContainer
    )

    # UseCases
    user_use_case: UserUseCaseContainer = providers.Container(
        UserUseCaseContainer,
        core=core,
        user_repo=user_repo,
        user_artist_repo=user_artist_repo,
        user_notification_repo=user_notification_repo,
        follow_repo=follow.repo,
        follow_use_case=follow.use_case,
        notification_repo=notification.repo,
        tendency_repo=tendency.repo,
        pod_repo=pod.pod_repo,
        user_state_service=user_state_service,
        user_dto_service=user_dto_service,
    )

    block_user_use_case: BlockUserUseCaseContainer = providers.Container(
        BlockUserUseCaseContainer,
        core=core,
        user_repo=user_repo,
        block_user_repo=block_user_repo,
        follow_repo=follow.repo,
        tendency_repo=tendency.repo,
    )

    user_notification_use_case: UserNotificationUseCaseContainer = providers.Container(
        UserNotificationUseCaseContainer,
        core=core,
        user_notification_repo=user_notification_repo,
        notification_service=notification.service,
    )

    user_artist_use_case: UserArtistUseCaseContainer = providers.Container(
        UserArtistUseCaseContainer,
        core=core,
        user_artist_repo=user_artist_repo,
        artist_repo=artist.repo,
    )
