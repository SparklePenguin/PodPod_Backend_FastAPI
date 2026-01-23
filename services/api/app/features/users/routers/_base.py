from app.common.abstract_router import AbstractApiLabel


class UserRouterRootLabel(AbstractApiLabel):
    PREFIX = "/users"
    TAG = "Users [BASE]"
    DESCRIPTION = "사용자 관리 API"


class UserCommonRouterLabel(AbstractApiLabel):
    PREFIX = "/users"
    TAG = "Users [Common]"
    DESCRIPTION = "사용자 공통 API"


class UserPreferredArtistsRouterLabel(AbstractApiLabel):
    PREFIX = "/preferred-artists"
    TAG = "Users [PREFERRED-ARTISTS]"
    DESCRIPTION = "사용자 선호 아티스트 API"


class UserNotificationRouterLabel(AbstractApiLabel):
    PREFIX = "/me/notifications"
    TAG = "Users [NOTIFICATIONS]"
    DESCRIPTION = "사용자 알림 API"


class UserFollowingsRouterLabel(AbstractApiLabel):
    PREFIX = "/me/followings"
    TAG = "Users [FOLLOWINGS]"
    DESCRIPTION = "사용자 팔로잉 API"


class BlockUserRouterLabel(AbstractApiLabel):
    PREFIX = "/blocks"
    TAG = "Users [BLOCKS]"
    DESCRIPTION = "사용자 차단 API"
