import time
import uuid
from datetime import datetime, timedelta
from enum import Enum

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

# 토큰 블랙리스트 (메모리 기반, 추후 Redis 등으로 대체 가능)
_token_blacklist = set()


def add_token_to_blacklist(token: str):
    """토큰을 블랙리스트에 추가"""
    _token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """토큰이 블랙리스트에 있는지 확인"""
    return token in _token_blacklist


def clear_blacklist():
    """블랙리스트 초기화 (테스트용)"""
    _token_blacklist.clear()


# - MARK: 토큰 만료
class TokenExpiredError(Exception):
    """토큰이 만료되었을 때"""

    status: int = 401
    code: str = "token_expired"
    message: str = "토큰이 만료되었습니다."


# - MARK: 서명 위조 / 잘못된 토큰일 때
class TokenInvalidError(Exception):
    """서명 위조 / 잘못된 토큰일 때"""

    status: int = 401
    code: str = "token_invalid"
    message: str = "서명 위조 / 잘못된 토큰입니다."


# - MARK: 토큰 디코딩 불가
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


# - MARK: 토큰 타입 Enum
class _TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


# - MARK: 토큰 만료일
_DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30분
_DEFAULT_REFRESH_TOKEN_EXPIRE_MINUTES = 7 * 24 * 60  # 7일 (분 단위)


# - MARK: 토큰 페이로드 모델
class _TokenPayload(BaseModel):
    sub: str  # 유저 식별자
    iat: float  # 발급 시간 (timestamp)
    exp: datetime  # 만료 시간
    jti: str  # 토큰 고유 ID
    type: _TokenType  # 토큰 타입


# - MARK: 액세스 토큰 생성 함수
def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """액세스 토큰 생성"""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=_DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = _TokenPayload(
        sub=str(user_id),
        iat=time.time(),
        exp=expire,
        jti=str(uuid.uuid4()),
        type=_TokenType.ACCESS,
    )
    return jwt.encode(
        payload.model_dump(), settings.secret_key, algorithm=settings.ALGORITHM
    )


# - MARK: 리프레시 토큰 생성 함수
def create_refresh_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """리프레시 토큰 생성"""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=_DEFAULT_REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    payload = _TokenPayload(
        sub=str(user_id),
        iat=time.time(),
        exp=expire,
        jti=str(uuid.uuid4()),
        type=_TokenType.REFRESH,
    )
    return jwt.encode(
        payload.model_dump(), settings.secret_key, algorithm=settings.ALGORITHM
    )


# - MARK: 액세스 토큰 검증 함수
def verify_token(token: str, token_type: str | None = None) -> int:
    """토큰 검증 후 user_id 리턴, 실패시 도메인 에러 발생"""
    # 블랙리스트 확인
    if is_token_blacklisted(token):
        raise TokenBlacklistedError()

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise TokenInvalidError()

        # 토큰 타입 검증 (지정된 경우)
        if token_type:
            actual_type = payload.get("type")
            if actual_type != token_type:
                raise TokenInvalidError()

        return int(user_id)

    except ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise TokenInvalidError()
    except Exception:
        raise TokenDecodeError()


def verify_refresh_token(token: str) -> int:
    """리프레시 토큰 전용 검증"""
    return verify_token(token, "refresh")


# - MARK: 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# - MARK: 비밀번호 해싱 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


# - MARK: 비밀번호 해싱 함수
def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)
