# 토큰 예외


class TokenExpiredError(Exception):
    """토큰이 만료되었을 때"""

    status: int = 401
    code: str = "token_expired"
    message: str = "토큰이 만료되었습니다."


class TokenInvalidError(Exception):
    """서명 위조 / 잘못된 토큰일 때"""

    status: int = 401
    code: str = "token_invalid"
    message: str = "서명 위조 / 잘못된 토큰입니다."


class TokenDecodeError(Exception):
    """JWT 디코딩 불가"""

    status: int = 401
    code: str = "token_decode_error"
    message: str = "JWT 디코딩 불가"


class TokenBlacklistedError(Exception):
    """토큰이 블랙리스트에 있을 때"""

    status: int = 401
    code: str = "token_blacklisted"
    message: str = "무효화된 토큰입니다."
