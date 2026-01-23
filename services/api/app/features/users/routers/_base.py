from app.common.abstract_router import AbstractRouterLabel


class UserRouterRootLabel(AbstractRouterLabel):
    PREFIX = "/users"
    TAG = "Users"
    DESCRIPTION = "사용자 관리 API"


class UserPreferredArtistsRouterLabel(AbstractRouterLabel):
    PREFIX = "/preferred-artists"
    TAG = "Users"
    DESCRIPTION = "선호 아티스트 API"
