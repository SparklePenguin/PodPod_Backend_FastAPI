from enum import Enum
import time
import uuid
from passlib.context import CryptContext
from jose import ExpiredSignatureError, JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel
from .config import settings


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


# - MARK: 토큰 타입 Enum
class _TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


# - MARK: 토큰 만료일
_DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 1
_DEFAULT_REFRESH_TOKEN_EXPIRE_MINUTES = 7


# - MARK: 토큰 페이로드 모델
class _TokenPayload(BaseModel):
    sub: str  # 유저 식별자
    iat: datetime  # 발급 시간
    exp: datetime  # 만료 시간
    jti: str  # 토큰 고유 ID
    type: _TokenType  # 토큰 타입


# - MARK: 액세스 토큰 생성 함수
def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=_DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = _TokenPayload(
        sub=str(user_id),
        iat=time.time(),
        exp=expire,
        jti=str(uuid.uuid4()),
        type=_TokenType.ACCESS,
    )
    return jwt.encode(payload.dict(), settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# - MARK: 리프레시 토큰 생성 함수
def create_refresh_token(
    user_id: int, expires_delta: Optional[timedelta] = None
) -> str:
    """리프레시 토큰 생성"""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=_DEFAULT_REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    payload = _TokenPayload(
        sub=str(user_id),
        iat=time.time(),
        exp=expire,
        jti=str(uuid.uuid4()),
        type=_TokenType.REFRESH,
    )
    return jwt.encode(payload.dict(), settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# - MARK: 액세스 토큰 검증 함수
def verify_token(token: str) -> int:
    """토큰 검증 후 user_id 리턴, 실패시 도메인 에러 발생"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise TokenInvalidError()
        return int(user_id)

    except ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise TokenInvalidError()
    except Exception:
        raise TokenDecodeError()


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
