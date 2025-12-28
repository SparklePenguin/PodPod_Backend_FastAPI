from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    """프로필 업데이트 요청"""

    nickname: str | None = Field(default=None)
    profile_image: str | None = Field(default=None, alias="profileImage")
    intro: str | None = Field(default=None)

    model_config = {
        "populate_by_name": True,
    }
