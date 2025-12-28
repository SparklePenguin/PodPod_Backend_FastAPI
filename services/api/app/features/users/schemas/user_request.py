from typing import List

from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    """프로필 업데이트 요청"""

    nickname: str | None = Field(default=None, serialization_alias="nickname")
    profile_image: str | None = Field(default=None, serialization_alias="profileImage")
    intro: str | None = Field(default=None, serialization_alias="intro")

    model_config = {
        "populate_by_name": True,
    }


class UpdateUserRequest(BaseModel):
    """멀티파트 프로필 업데이트 요청"""

    nickname: str | None = Field(default=None, serialization_alias="nickname")
    intro: str | None = Field(default=None, serialization_alias="intro")

    model_config = {"populate_by_name": True}


class UpdatePreferredArtistsRequest(BaseModel):
    """선호 아티스트 요청"""

    artist_ids: List[int] = Field(default=[], serialization_alias="artistIds")

    model_config = {
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }


class AcceptTermsRequest(BaseModel):
    """약관 동의 요청"""

    terms_accepted: bool = Field(
        default=True, serialization_alias="termsAccepted", description="약관 동의 여부"
    )

    model_config = {"populate_by_name": True}
