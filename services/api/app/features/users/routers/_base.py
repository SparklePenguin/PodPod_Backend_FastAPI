from fastapi import APIRouter

from app.common.abstract_router import AbstractApiLabel


class UserController(AbstractApiLabel):
    PREFIX = "/users"
    TAG = "Users [BASE]"
    DESCRIPTION = "사용자 관리 API"

    ROUTER = APIRouter(
        prefix=PREFIX,
        tags=[TAG]
    )


class UserCommonController(AbstractApiLabel):
    PREFIX = "/users"
    TAG = "Users [Common]"
    DESCRIPTION = "사용자 공통 API"

    ROUTER = APIRouter(
        prefix=UserController.PREFIX,
        tags=[TAG]
    )


class UserPreferredArtistsController(AbstractApiLabel):
    PREFIX = "/preferred-artists"
    TAG = "Users [PREFERRED-ARTISTS]"
    DESCRIPTION = "사용자 선호 아티스트 API"

    ROUTER = APIRouter(
        prefix=f"{UserController.PREFIX}",
        tags=[TAG]
    )


class UserNotificationController(AbstractApiLabel):
    PREFIX = "/notifications"
    TAG = "Users [NOTIFICATIONS]"
    DESCRIPTION = "사용자 알림 API"

    ROUTER = APIRouter(
        prefix=f"{UserController.PREFIX}",
        tags=[TAG]
    )


class UserFollowingsController(AbstractApiLabel):
    PREFIX = "/followings"
    TAG = "Users [FOLLOWINGS]"
    DESCRIPTION = "사용자 팔로잉 API"

    ROUTER = APIRouter(
        prefix=f"{UserController.PREFIX}",
        tags=[TAG]
    )


class BlockUserController(AbstractApiLabel):
    PREFIX = "/blocks"
    TAG = "Users [BLOCKS]"
    DESCRIPTION = "사용자 차단 API"

    ROUTER = APIRouter(
        prefix=f"{UserController.PREFIX}",
        tags=[TAG]
    )
