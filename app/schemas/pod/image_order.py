from typing import Optional
from pydantic import BaseModel, Field


class ImageOrder(BaseModel):
    """이미지 순서 정보"""

    type: str = Field(..., description="이미지 타입: 'existing' 또는 'new'")
    url: Optional[str] = Field(
        None, description="기존 이미지 URL (type='existing'일 때)"
    )
    file_index: Optional[int] = Field(
        None, alias="fileIndex", description="새 이미지 파일 인덱스 (type='new'일 때)"
    )

    model_config = {"populate_by_name": True}
