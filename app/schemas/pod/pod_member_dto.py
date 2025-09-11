from pydantic import BaseModel, Field


class PodMemberDto(BaseModel):
    user_id: int = Field(alias="userId")
    role: str = Field(alias="role")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
