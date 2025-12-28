from pydantic import BaseModel, Field


class UpdateUserRequest(BaseModel):
    """멀티파트 프로필 업데이트 요청"""

    nickname: str | None = Field(default=None)
    intro: str | None = Field(default=None)

    model_config = {"populate_by_name": True}
