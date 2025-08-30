import datetime
from typing import List, Optional
from pydantic import BaseModel


# - MARK: 사용자 정보 응답
class UserDto(BaseModel):
    id: int  # 필수값
    email: Optional[str] = None
    username: Optional[str] = None
    nickname: Optional[str] = None
    profile_image: Optional[str] = None
    intro: Optional[str] = None
    needs_onboarding: bool  # 필수값

    model_config = {"from_attributes": True}


# - MARK: 프로필 업데이트 요청
class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    profile_image: Optional[str] = None
    intro: Optional[str] = None


# - MARK: 선호 아티스트 요청
class UpdatePreferredArtistsRequest(BaseModel):
    artist_ids: List[int] = []
