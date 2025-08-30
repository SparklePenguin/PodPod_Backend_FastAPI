import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# - MARK: 사용자 정보 응답
class UserDto(BaseModel):
    id: int = Field(alias="id")  # 필수값
    email: Optional[str] = Field(default=None, alias="email")
    username: Optional[str] = Field(default=None, alias="username")
    nickname: Optional[str] = Field(default=None, alias="nickname")
    profile_image: Optional[str] = Field(default=None, alias="profileImage")
    intro: Optional[str] = Field(default=None, alias="intro")
    needs_onboarding: bool = Field(alias="needsOnboarding")  # 필수값
    created_at: Optional[datetime.datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime.datetime] = Field(default=None, alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }


# - MARK: 프로필 업데이트 요청
class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(default=None, alias="username")
    profile_image: Optional[str] = Field(default=None, alias="profileImage")
    intro: Optional[str] = Field(default=None, alias="intro")

    model_config = {
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }


# - MARK: 선호 아티스트 요청
class UpdatePreferredArtistsRequest(BaseModel):
    artist_ids: List[int] = Field(default=[], alias="artistIds")

    model_config = {
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }
