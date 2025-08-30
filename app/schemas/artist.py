# - MARK: 아티스트 정보 응답
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# - MARK: 아티스트 정보 응답
class ArtistDto(BaseModel):
    id: int  # 필수값
    type: Optional[str] = None
    name: str  # 필수값
    profile_image: Optional[str] = None

    model_config = {"from_attributes": True}
