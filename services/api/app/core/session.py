"""세션 및 토큰 관리 (Redis 기반)"""

import time
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel

from app.deps.redis import get_redis_client
from .config import settings
from .exceptions.token_exception import (
    TokenInvalidError,
    TokenExpiredError,
    TokenDecodeError,
    TokenBlacklistedError
)


class TokenType(str, Enum):
    """ 토큰 타입 """
    ACCESS = "access"
    REFRESH = "refresh"


class _TokenPayload(BaseModel):
    sub: str  # 유저 식별자
    iat: float  # 발급 시간 (timestamp)
    exp: datetime  # 만료 시간
    jti: str  # 토큰 고유 ID
    type: TokenType  # 토큰 타입


# - MARK: 블랙리스트 관리


async def add_token_to_blacklist(token: str, ttl_seconds: int = 3600):
    """토큰을 블랙리스트에 추가 (Redis)"""
    redis = await get_redis_client()
    await redis.setex(f"blacklist:{token}", ttl_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    """토큰이 블랙리스트에 있는지 확인 (Redis)"""
    redis = await get_redis_client()
    result = await redis.get(f"blacklist:{token}")
    return result is not None


class TokenManager:
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30분
    DEFAULT_REFRESH_TOKEN_EXPIRE_MINUTES = 7 * 24 * 60  # 7일 (분 단위)

    def __init__(self):
        self.secret_key = settings.jwt.secret_key
        self.algorithm = settings.jwt.algorithm

        self._access_expire_time = datetime.now(timezone.utc) + timedelta(
            minutes=self.DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self._refresh_expire_time = datetime.now(timezone.utc) + timedelta(
            minutes=self.DEFAULT_REFRESH_TOKEN_EXPIRE_MINUTES
        )

    def _generate_token(self, payload: _TokenPayload):
        return jwt.encode(
            payload.model_dump(),
            self.secret_key,
            algorithm=self.algorithm
        )

    def create_access_token(self, user_id: int) -> str:
        """액세스 토큰 생성"""
        return self._generate_token(
            _TokenPayload(
                sub=str(user_id),
                iat=time.time(),
                exp=self._access_expire_time,
                jti=str(uuid.uuid4()),
                type=TokenType.ACCESS,
            ))

    async def create_refresh_token(self, user_id: int) -> str:
        """리프레시 토큰 생성 및 Redis에 저장"""
        _paylaod = _TokenPayload(
            sub=str(user_id),
            iat=time.time(),
            exp=self._refresh_expire_time,
            jti=str(uuid.uuid4()),
            type=TokenType.REFRESH,
        )
        # Redis에 저장 (key: refresh_token:{jti}, value: user_id, TTL: 7일)
        redis = await get_redis_client()

        ttl_seconds = int(self._refresh_expire_time.timestamp())

        await redis.setex(f"refresh_token:{_paylaod.jti}", ttl_seconds, str(user_id))

        return self._generate_token(_paylaod)

    async def revoke_refresh_token(self, token: str) -> None:
        """리프레시 토큰 무효화 (Redis에서 삭제)"""
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            jti: str | None = payload.get("jti")
            if jti:
                redis = await get_redis_client()
                await redis.delete(f"refresh_token:{jti}")
        except Exception:
            pass  # 토큰 디코드 실패해도 무시

    async def verify_refresh_token(self, token: str) -> int:
        """리프레시 토큰 전용 검증"""
        return await self.verify_token(token, TokenType.REFRESH.value)

    # - MARK: 토큰 검증
    async def verify_token(self, token: str, token_type: str | None = None) -> int:
        """토큰 검증 후 user_id 리턴, 실패시 도메인 에러 발생"""
        # 블랙리스트 확인
        if await is_token_blacklisted(token):
            raise TokenBlacklistedError()

        try:
            payload = jwt.decode(
                token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm]
            )
            user_id: str | None = payload.get("sub")
            jti: str | None = payload.get("jti")

            if not user_id:
                raise TokenInvalidError()

            # 토큰 타입 검증 (지정된 경우)
            if token_type:
                actual_type = payload.get("type")
                if actual_type != token_type:
                    raise TokenInvalidError()

                # 리프레시 토큰인 경우 Redis에서 확인
                if token_type == "refresh" and jti:
                    redis = await get_redis_client()
                    stored_user_id = await redis.get(f"refresh_token:{jti}")
                    if stored_user_id is None:
                        raise TokenInvalidError()  # Redis에 없으면 무효화된 토큰
                    if stored_user_id != user_id:
                        raise TokenInvalidError()  # user_id 불일치

            return int(user_id)

        except ExpiredSignatureError:
            raise TokenExpiredError()
        except JWTError:
            raise TokenInvalidError()
        except Exception:
            raise TokenDecodeError()


# - MARK: OAuth State 관리


async def save_oauth_state(state: str, expire_seconds: int = 600):
    """OAuth state를 Redis에 저장 (기본 10분)"""
    redis = await get_redis_client()
    await redis.set(f"oauth:state:{state}", "valid", ex=expire_seconds)


async def verify_oauth_state(state: str, redis=None) -> bool:
    """OAuth state 검증 및 삭제 (일회용)"""
    if redis is None:
        redis = await get_redis_client()
    key = f"oauth:state:{state}"
    exists = await redis.exists(key)
    if exists:
        await redis.delete(key)  # 사용 후 삭제 (CSRF 재사용 방지)
        return True
    return False
