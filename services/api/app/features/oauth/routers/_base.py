from app.common.abstract_router import AbstractApiLabel


class OAuthRouterRootLabel(AbstractApiLabel):
    PREFIX = "/oauth"
    TAG = "OAUTH"
    DESCRIPTION = "OAUTH 인증 API"


class GoogleOauthRouterLabel(AbstractApiLabel):
    PREFIX = "/google"
    TAG = "OAuth [Google]"
    DESCRIPTION = "Google OAUTH 인증 API"


class KaKoOauthRouterLabel(AbstractApiLabel):
    PREFIX = "/kakao"
    TAG = "OAuth [KaKao]"
    DESCRIPTION = "KaKao OAUTH 인증 API"


class AppleOauthRouterLabel(AbstractApiLabel):
    PREFIX = "/apple"
    TAG = "OAuth [Apple]"
    DESCRIPTION = "Apple OAUTH 인증 API"
