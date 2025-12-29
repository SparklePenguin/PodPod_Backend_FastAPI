from pydantic import BaseModel, Field


class UserDto(BaseModel):
    """간단한 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID")
    nickname: str = Field(..., description="닉네임")
    profile_image: str = Field(
        ..., alias="profileImage", description="프로필 이미지 URL"
    )
    intro: str = Field(..., description="자기소개")
    tendency_type: str = Field(..., alias="tendencyType", description="덕메 성향 타입")
    is_following: bool = Field(
        default=False, alias="isFollowing", description="팔로우 여부"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
