from pydantic import BaseModel, Field


class AcceptTermsRequest(BaseModel):
    """약관 동의 요청"""

    terms_accepted: bool = Field(
        default=True, alias="termsAccepted", description="약관 동의 여부"
    )

    model_config = {"populate_by_name": True}
