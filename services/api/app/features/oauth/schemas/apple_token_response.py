from pydantic import BaseModel, Field


class AppleTokenResponse(BaseModel):
    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(serialization_alias="tokenType", default="Bearer")
    expires_in: int = Field(serialization_alias="expiresIn")
    refresh_token: str = Field(serialization_alias="refreshToken")
    id_token: str = Field(serialization_alias="idToken")

    model_config = {
        "populate_by_name": True,
    }
