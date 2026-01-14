"""Dependency Injection Containers

새로운 구조:
- 모든 FeatureContainer가 application_container.py에 정의됨
- 중첩 컨테이너 대신 필요한 의존만 직접 주입
- 레벨별 의존 관계가 명시적으로 표현됨

사용법:
    from app.core.containers import container
    
    # UseCase 접근
    container.auth_feature.oauth_use_case()
    container.user_feature.user_use_case()
"""

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
from app.core.containers.core_container import CoreContainer

__all__ = [
    # Application
    "ApplicationContainer",
    "container",
    # Core
    "CoreContainer",
    # Feature Containers (Level 1)
    "TendencyFeatureContainer",
    "ArtistFeatureContainer",
    "SessionFeatureContainer",
    "LocationFeatureContainer",
    "FollowFeatureContainer",
    # Feature Containers (Level 2)
    "NotificationFeatureContainer",
    "PodFeatureContainer",
    "ChatFeatureContainer",
    # Feature Containers (Level 3)
    "UserFeatureContainer",
    # Feature Containers (Level 4)
    "AuthFeatureContainer",
    "ReportFeatureContainer",
]
