"""Pod Form 의존성 함수"""

import json
from datetime import datetime
from typing import List

from app.features.pods.schemas.pod_schemas import PodForm
from fastapi import Form


async def get_pod_form(
    title: str | None = Form(None),
    description: str | None = Form(None),
    subCategories: List[str] = Form(..., description="서브 카테고리 리스트 (필수)"),
    capacity: int | None = Form(None),
    place: str | None = Form(None),
    address: str | None = Form(None),
    subAddress: str | None = Form(None),
    x: float | None = Form(None),
    y: float | None = Form(None),
    meetingDate: datetime | None = Form(None, description="만남 일시 (UTC ISO 8601)"),
    selectedArtistId: int | None = Form(None),
    imageOrders: str | None = Form(None),
) -> PodForm:
    """PodForm을 Form 데이터로부터 생성"""
    # subCategories를 JSON 문자열로 변환 (PodForm이 문자열을 기대하므로)
    sub_categories_json = json.dumps(subCategories) if subCategories else None
    
    return PodForm(
        title=title,
        description=description,
        sub_categories=sub_categories_json,
        capacity=capacity,
        place=place,
        address=address,
        sub_address=subAddress,
        x=x,
        y=y,
        meeting_date=meetingDate,
        selected_artist_id=selectedArtistId,
        image_orders=imageOrders,
    )
