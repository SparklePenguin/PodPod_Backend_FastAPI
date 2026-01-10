"""Dependency Injection Containers"""

from app.core.containers.application_container import (
    ApplicationContainer,
    ArtistFeatureContainer,
    AuthFeatureContainer,
    ChatFeatureContainer,
    FollowFeatureContainer,
    LocationFeatureContainer,
    NotificationFeatureContainer,
    PodFeatureContainer,
    ReportFeatureContainer,
    SessionFeatureContainer,
    TendencyFeatureContainer,
    UserFeatureContainer,
    container,
)
from app.core.containers.artist_container import (
    ArtistContainer,
    ArtistRepoContainer,
    CreateArtistSuggestionUseCaseContainer,
    GetArtistRankingUseCaseContainer,
    GetArtistsUseCaseContainer,
    GetArtistUseCaseContainer,
    GetScheduleByIdUseCaseContainer,
    GetSchedulesUseCaseContainer,
    GetSuggestionByIdUseCaseContainer,
    GetSuggestionsByArtistNameUseCaseContainer,
    GetSuggestionsUseCaseContainer,
)
from app.core.containers.auth_container import (
    AppleOAuthServiceContainer,
    AuthContainer,
    AuthServiceContainer,
    GoogleOAuthServiceContainer,
    KakaoOAuthServiceContainer,
    NaverOAuthServiceContainer,
    OAuthUseCaseContainer,
)
from app.core.containers.chat_container import (
    ChatContainer,
    ChatMessageServiceContainer,
    ChatNotificationServiceContainer,
    ChatPodRepoContainer,
    ChatPodServiceContainer,
    ChatRepoContainer,
    ChatRoomRepoContainer,
    ChatRoomUseCaseContainer,
    ChatUseCaseContainer,
    ChatUserRepoContainer,
)
from app.core.containers.core_container import CoreContainer
from app.core.containers.follow_container import (
    FollowContainer,
    FollowRepoContainer,
    FollowUseCaseContainer,
)
from app.core.containers.location_container import (
    LocationContainer,
    LocationUseCaseContainer,
)
from app.core.containers.notification_container import (
    NotificationContainer,
    NotificationDtoServiceContainer,
    NotificationRepoContainer,
    NotificationUseCaseContainer,
)
from app.core.containers.pod_container import (
    ApplicationDtoServiceContainer,
    ApplicationNotificationServiceContainer,
    ApplicationRepoContainer,
    ApplicationUseCaseContainer,
    LikeNotificationServiceContainer,
    LikeUseCaseContainer,
    PodContainer,
    PodEnrichmentServiceContainer,
    PodLikeRepoContainer,
    PodNotificationServiceContainer,
    PodQueryUseCaseContainer,
    PodRepoContainer,
    PodReviewRepoContainer,
    PodUseCaseContainer,
    PodUserRepoContainer,
    ReviewDtoServiceContainer,
    ReviewNotificationServiceContainer,
    ReviewUseCaseContainer,
)
from app.core.containers.report_container import (
    ReportContainer,
    ReportUseCaseContainer,
)
from app.core.containers.session_container import (
    SessionContainer,
    SessionRepoContainer,
    SessionUseCaseContainer,
)
from app.core.containers.tendency_container import (
    TendencyCalculationServiceContainer,
    TendencyContainer,
    TendencyRepoContainer,
    TendencyUseCaseContainer,
)
from app.core.containers.user_container import (
    BlockUserRepoContainer,
    BlockUserUseCaseContainer,
    UserArtistRepoContainer,
    UserArtistUseCaseContainer,
    UserContainer,
    UserDtoServiceContainer,
    UserNotificationRepoContainer,
    UserNotificationUseCaseContainer,
    UserRepoContainer,
    UserReportRepoContainer,
    UserStateServiceContainer,
    UserUseCaseContainer,
)

__all__ = [
    # Application
    "ApplicationContainer",
    "container",
    # Feature Containers
    "TendencyFeatureContainer",
    "ArtistFeatureContainer",
    "SessionFeatureContainer",
    "LocationFeatureContainer",
    "FollowFeatureContainer",
    "NotificationFeatureContainer",
    "PodFeatureContainer",
    "ChatFeatureContainer",
    "UserFeatureContainer",
    "AuthFeatureContainer",
    "ReportFeatureContainer",
    # Core
    "CoreContainer",
    # User
    "UserContainer",
    "UserRepoContainer",
    "UserArtistRepoContainer",
    "BlockUserRepoContainer",
    "UserNotificationRepoContainer",
    "UserReportRepoContainer",
    "UserDtoServiceContainer",
    "UserStateServiceContainer",
    "UserUseCaseContainer",
    "BlockUserUseCaseContainer",
    "UserNotificationUseCaseContainer",
    "UserArtistUseCaseContainer",
    # Auth
    "AuthContainer",
    "AuthServiceContainer",
    "KakaoOAuthServiceContainer",
    "GoogleOAuthServiceContainer",
    "AppleOAuthServiceContainer",
    "NaverOAuthServiceContainer",
    "OAuthUseCaseContainer",
    # Notification
    "NotificationContainer",
    "NotificationRepoContainer",
    "NotificationDtoServiceContainer",
    "NotificationUseCaseContainer",
    # Follow
    "FollowContainer",
    "FollowRepoContainer",
    "FollowUseCaseContainer",
    # Tendency
    "TendencyContainer",
    "TendencyRepoContainer",
    "TendencyCalculationServiceContainer",
    "TendencyUseCaseContainer",
    # Artist
    "ArtistContainer",
    "ArtistRepoContainer",
    "GetArtistUseCaseContainer",
    "GetArtistsUseCaseContainer",
    "GetScheduleByIdUseCaseContainer",
    "GetSchedulesUseCaseContainer",
    "CreateArtistSuggestionUseCaseContainer",
    "GetSuggestionByIdUseCaseContainer",
    "GetSuggestionsUseCaseContainer",
    "GetArtistRankingUseCaseContainer",
    "GetSuggestionsByArtistNameUseCaseContainer",
    # Session
    "SessionContainer",
    "SessionRepoContainer",
    "SessionUseCaseContainer",
    # Location
    "LocationContainer",
    "LocationUseCaseContainer",
    # Pod
    "PodContainer",
    "PodRepoContainer",
    "ApplicationRepoContainer",
    "PodLikeRepoContainer",
    "PodReviewRepoContainer",
    "PodUserRepoContainer",
    "ReviewDtoServiceContainer",
    "ApplicationDtoServiceContainer",
    "LikeNotificationServiceContainer",
    "ReviewNotificationServiceContainer",
    "ApplicationNotificationServiceContainer",
    "PodNotificationServiceContainer",
    "PodEnrichmentServiceContainer",
    "ApplicationUseCaseContainer",
    "LikeUseCaseContainer",
    "ReviewUseCaseContainer",
    "PodQueryUseCaseContainer",
    "PodUseCaseContainer",
    # Chat
    "ChatContainer",
    "ChatRepoContainer",
    "ChatRoomRepoContainer",
    "ChatUserRepoContainer",
    "ChatPodRepoContainer",
    "ChatMessageServiceContainer",
    "ChatPodServiceContainer",
    "ChatNotificationServiceContainer",
    "ChatRoomUseCaseContainer",
    "ChatUseCaseContainer",
    # Report
    "ReportContainer",
    "ReportUseCaseContainer",
]
