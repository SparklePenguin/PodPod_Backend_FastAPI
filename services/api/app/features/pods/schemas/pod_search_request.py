import datetime
from typing import List

from pydantic import BaseModel, Field, model_validator


class PodSearchRequest(BaseModel):
    """팟 검색 요청"""

    title: str | None = Field(None, description="팟 제목")
    main_category: str | None = Field(
        None,
        alias="mainCategory",
        description="메인 카테고리 (ACCOMPANY, GOODS, TOUR, ETC)",
    )
    sub_category: str | None = Field(
        None, alias="subCategory", description="서브 카테고리"
    )
    start_date: datetime.date | None = Field(
        None, alias="startDate", description="시작 날짜"
    )
    end_date: datetime.date | None = Field(
        None, alias="endDate", description="종료 날짜"
    )
    location: List[str | None] = Field(
        None,
        description="지역 리스트 (address 또는 sub_address에 포함)",
    )
    page: int | None = Field(1, ge=1, description="페이지 번호")
    page_size: int | None = Field(
        20, alias="pageSize", ge=1, le=100, description="페이지 크기"
    )
    limit: int | None = Field(
        None,
        description="결과 제한 (deprecated, pageSize 사용 권장)",
    )

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, values):
        """null 값을 기본값으로 변경"""
        if isinstance(values, dict):
            if values.get("page") is None:
                values["page"] = 1
            if values.get("pageSize") is None:
                values["pageSize"] = 20
        return values

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
