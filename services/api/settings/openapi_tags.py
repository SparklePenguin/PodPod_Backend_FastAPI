from app.features.oauth.routers import GoogleOauthController, KaKoOauthController, AppleOauthController
from app.features.users.routers import (
    UserController,
    UserPreferredArtistsController,
    UserCommonController,
    UserNotificationController, \
    UserFollowingsController,
    BlockUserController
)

API_TAGS = []

# OAUTH ROUTER
API_TAGS.extend([
    router.to_dict() for router in [
        GoogleOauthController,
        KaKoOauthController,
        AppleOauthController
    ]
])
# USER ROUTER
API_TAGS.extend([
    router.to_dict() for router in [
        UserController,
        UserCommonController,
        UserPreferredArtistsController,
        UserNotificationController,
        UserFollowingsController,
        BlockUserController
    ]
])

API_TAGS.extend([
    {
        "name": "session",
        "description": "세션 관리 API (로그인/로그아웃)",
    },
    {
        "name": "artists",
        "description": "아티스트 관리 API",
    },
    {
        "name": "artist-schedules",
        "description": "아티스트 스케줄 API",
    },
    {
        "name": "tendencies",
        "description": "성향 테스트 API",
    },
    {
        "name": "surveys",
        "description": "설문 조사 API",
    },
    {
        "name": "pods",
        "description": "파티(Pod) 관리 API",
    },
    {
        "name": "follow",
        "description": "팔로우 관리 API",
    },
    {
        "name": "notifications",
        "description": "알림 API",
    },
    {
        "name": "regions",
        "description": "지역 관리 API",
    },
    {
        "name": "reports",
        "description": "신고 API",
    },
    {
        "name": "profile-images",
        "description": "랜덤 프로필 이미지 API",
    },
    {
        "name": "chat",
        "description": "채팅 API",
    },
    {
        "name": "health",
        "description": "시스템 헬스체크 API",
    },
    {
        "name": "applications",
        "description": "파티 신청서 관리 API",
    },
    {
        "name": "reviews",
        "description": "파티 후기 API",
    },
    {
        "name": "admin",
        "description": "관리자 API",
    },
    {
        "name": "artist-suggestions",
        "description": "아티스트 추천 API",
    }
]
)
