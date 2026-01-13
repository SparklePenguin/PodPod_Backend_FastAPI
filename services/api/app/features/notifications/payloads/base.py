"""알림 Payload 공통 Ref 정의"""

from pydantic import BaseModel, Field


class PodRef(BaseModel):
    """파티 참조 정보"""

    pod_id: int = Field(description="파티 ID")
    party_name: str = Field(description="파티 이름")


class UserRef(BaseModel):
    """유저 참조 정보"""

    user_id: int = Field(description="유저 ID")
    nickname: str = Field(description="유저 닉네임")


class ReviewRef(BaseModel):
    """리뷰 참조 정보"""

    review_id: int = Field(description="리뷰 ID")
