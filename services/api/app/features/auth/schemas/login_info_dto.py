from app.features.auth.schemas.credential_dto import CredentialDto
from app.features.users.schemas import UserDetailDto
from pydantic import BaseModel


class LoginInfoDto(BaseModel):
    """로그인 정보 응답 DTO"""

    credential: CredentialDto
    user: UserDetailDto
