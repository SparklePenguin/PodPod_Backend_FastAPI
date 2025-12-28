from pydantic import BaseModel, Field


class AppleTokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(alias="tokenType", default="Bearer")
    expires_in: int = Field(alias="expiresIn")
    refresh_token: str = Field(alias="refreshToken")
    id_token: str = Field(alias="idToken")

    model_config = {
        "populate_by_name": True,
    }
