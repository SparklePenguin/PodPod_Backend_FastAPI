"""비밀번호 해싱 및 보안 유틸리티"""

from passlib.context import CryptContext

# - MARK: 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# - MARK: 비밀번호 검증
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


# - MARK: 비밀번호 해싱
def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)
