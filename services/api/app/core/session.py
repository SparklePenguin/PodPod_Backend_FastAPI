def blacklist_token(token: str, expire_seconds: int, redis):
    """토큰 블랙리스트에 추가"""
    redis.set(token, "blacklisted", ex=expire_seconds)


async def blacklist_token_async(token: str, expire_seconds: int, redis):
    """토큰 블랙리스트에 추가 (비동기)"""
    await redis.set(token, "blacklisted", ex=expire_seconds)


def is_token_blacklisted(token: str, redis) -> bool:
    """토큰이 블랙리스트에 있는지 확인"""
    return redis.exists(token) > 0


# OAuth State 관리
async def save_oauth_state(state: str, redis, expire_seconds: int = 600):
    """OAuth state를 Redis에 저장 (기본 10분)"""
    await redis.set(f"oauth:state:{state}", "valid", ex=expire_seconds)


async def verify_oauth_state(state: str, redis) -> bool:
    """OAuth state 검증 및 삭제 (일회용)"""
    key = f"oauth:state:{state}"
    exists = await redis.exists(key)
    if exists:
        await redis.delete(key)  # 사용 후 삭제 (CSRF 재사용 방지)
        return True
    return False
