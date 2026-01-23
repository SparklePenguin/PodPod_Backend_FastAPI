from fastapi import APIRouter

from app.common.abstract_router import AbstractController


class OAuthController(AbstractController):
    PREFIX = "/oauth"
    TAG = "OAUTH"
    DESCRIPTION = "OAUTH 인증 API"

    ROUTER = APIRouter(
        prefix=PREFIX,
        tags=[TAG]
    )


class GoogleOauthController(AbstractController):
    PREFIX = "/google"
    TAG = "OAuth [Google]"
    DESCRIPTION = "Google OAUTH 인증 API"

    ROUTER = APIRouter(
        prefix=OAuthController.PREFIX,
        tags=[TAG]
    )


class KaKoOauthController(AbstractController):
    PREFIX = "/kakao"
    TAG = "OAuth [KaKao]"
    DESCRIPTION = "KaKao OAUTH 인증 API"

    ROUTER = APIRouter(
        prefix=OAuthController.PREFIX,
        tags=[TAG]
    )


class AppleOauthController(AbstractController):
    PREFIX = "/apple"
    TAG = "OAuth [Apple]"
    DESCRIPTION = "Apple OAUTH 인증 API"

    ROUTER = APIRouter(
        prefix=OAuthController.PREFIX,
        tags=[TAG]
    )
