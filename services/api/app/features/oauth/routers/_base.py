from enum import Enum


class OAuthRouterLabel(Enum):
    PREFIX = "/oauth"
    TAG = "OAUTH"
    DESCRIPTION = "OAUTH 인증 API"

    @classmethod
    def to_dict(cls):
        return {
            "name": cls.TAG.value,
            "description": cls.DESCRIPTION.value
        }
