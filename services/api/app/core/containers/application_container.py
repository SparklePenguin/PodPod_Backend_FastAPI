"""Application Container - 모든 Feature Container 조립"""

from dependency_injector import containers, providers


# MARK: - Level 1: Core만 의존하는 Feature Containers
class TendencyFeatureContainer(containers.DeclarativeContainer):
    """성향 Feature 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.tendency_container import TendencyContainer

    core: CoreContainer = providers.DependenciesContainer()

    tendency: TendencyContainer = providers.Container(TendencyContainer, core=core)


class ArtistFeatureContainer(containers.DeclarativeContainer):
    """아티스트 Feature 컨테이너"""

    from app.core.containers.artist_container import ArtistContainer
    from app.core.containers.core_container import CoreContainer

    core: CoreContainer = providers.DependenciesContainer()

    artist: ArtistContainer = providers.Container(ArtistContainer, core=core)


class SessionFeatureContainer(containers.DeclarativeContainer):
    """세션 Feature 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.session_container import SessionContainer

    core: CoreContainer = providers.DependenciesContainer()

    session: SessionContainer = providers.Container(SessionContainer, core=core)


class LocationFeatureContainer(containers.DeclarativeContainer):
    """위치 Feature 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.location_container import LocationContainer

    core: CoreContainer = providers.DependenciesContainer()

    location: LocationContainer = providers.Container(LocationContainer, core=core)


class FollowFeatureContainer(containers.DeclarativeContainer):
    """팔로우 Feature 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowContainer

    core: CoreContainer = providers.DependenciesContainer()

    follow: FollowContainer = providers.Container(FollowContainer, core=core)


# MARK: - Level 2: Core + Level1 의존
class NotificationFeatureContainer(containers.DeclarativeContainer):
    """알림 Feature 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.notification_container import NotificationContainer

    core: CoreContainer = providers.DependenciesContainer()

    notification: NotificationContainer = providers.Container(
        NotificationContainer,
        core=core,
    )


class PodFeatureContainer(containers.DeclarativeContainer):
    """파티 Feature 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.pod_container import PodContainer

    core: CoreContainer = providers.DependenciesContainer()

    pod: PodContainer = providers.Container(
        PodContainer,
        core=core,
    )


class ChatFeatureContainer(containers.DeclarativeContainer):
    """채팅 Feature 컨테이너"""

    from app.core.containers.chat_container import ChatContainer
    from app.core.containers.core_container import CoreContainer

    core: CoreContainer = providers.DependenciesContainer()

    chat: ChatContainer = providers.Container(ChatContainer, core=core)


# MARK: - Level 3: 여러 Feature 의존
class UserFeatureContainer(containers.DeclarativeContainer):
    """사용자 Feature 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.user_container import UserContainer

    core: CoreContainer = providers.DependenciesContainer()

    user: UserContainer = providers.Container(
        UserContainer,
        core=core,
    )


# MARK: - Level 4: User 의존
class AuthFeatureContainer(containers.DeclarativeContainer):
    """인증 Feature 컨테이너"""

    from app.core.containers.auth_container import AuthContainer
    from app.core.containers.core_container import CoreContainer

    core: CoreContainer = providers.DependenciesContainer()

    auth: AuthContainer = providers.Container(
        AuthContainer,
        core=core,
    )


class ReportFeatureContainer(containers.DeclarativeContainer):
    """신고 Feature 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.report_container import ReportContainer

    core: CoreContainer = providers.DependenciesContainer()

    report: ReportContainer = providers.Container(
        ReportContainer,
        core=core,
    )


# MARK: - Aggregate Container
class ApplicationContainer(containers.DeclarativeContainer):
    """애플리케이션 최상위 컨테이너 - 모든 Feature Container 조립"""

    from app.core.containers.artist_container import ArtistContainer
    from app.core.containers.auth_container import AuthContainer
    from app.core.containers.chat_container import ChatContainer
    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowContainer
    from app.core.containers.location_container import LocationContainer
    from app.core.containers.notification_container import NotificationContainer
    from app.core.containers.pod_container import PodContainer
    from app.core.containers.report_container import ReportContainer
    from app.core.containers.session_container import SessionContainer
    from app.core.containers.tendency_container import TendencyContainer
    from app.core.containers.user_container import UserContainer

    # Core Infrastructure
    core: CoreContainer = providers.Container(CoreContainer)

    # Level 1: Independent Feature Containers (core만 의존)
    tendency_feature: TendencyFeatureContainer = providers.Container(
        TendencyFeatureContainer, core=core
    )
    artist_feature: ArtistFeatureContainer = providers.Container(
        ArtistFeatureContainer, core=core
    )
    session_feature: SessionFeatureContainer = providers.Container(
        SessionFeatureContainer, core=core
    )
    location_feature: LocationFeatureContainer = providers.Container(
        LocationFeatureContainer, core=core
    )
    follow_feature: FollowFeatureContainer = providers.Container(
        FollowFeatureContainer, core=core
    )

    # Level 2: Core + Level1 의존
    notification_feature: NotificationFeatureContainer = providers.Container(
        NotificationFeatureContainer,
        core=core,
    )
    pod_feature: PodFeatureContainer = providers.Container(
        PodFeatureContainer,
        core=core,
    )
    chat_feature: ChatFeatureContainer = providers.Container(
        ChatFeatureContainer,
        core=core,
    )

    # Level 3: 여러 Feature 의존
    user_feature: UserFeatureContainer = providers.Container(
        UserFeatureContainer,
        core=core,
    )

    # Level 4: User 의존
    auth_feature: AuthFeatureContainer = providers.Container(
        AuthFeatureContainer,
        core=core,
    )
    report_feature: ReportFeatureContainer = providers.Container(
        ReportFeatureContainer,
        core=core,
    )

    # 편의를 위한 alias (기존 호환성 유지)
    tendency: TendencyContainer = tendency_feature.tendency
    artist: ArtistContainer = artist_feature.artist
    session: SessionContainer = session_feature.session
    location: LocationContainer = location_feature.location
    follow: FollowContainer = follow_feature.follow
    notification: NotificationContainer = notification_feature.notification
    pod: PodContainer = pod_feature.pod
    chat: ChatContainer = chat_feature.chat
    user: UserContainer = user_feature.user
    auth: AuthContainer = auth_feature.auth
    report: ReportContainer = report_feature.report


# 전역 컨테이너 인스턴스
container = ApplicationContainer()
