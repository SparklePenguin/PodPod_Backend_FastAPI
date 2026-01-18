"""Pod Form 의존성 함수"""

import json
from datetime import datetime
from typing import List

from app.features.pods.schemas.pod_schemas import PodForm
from fastapi import Form


async def get_pod_form(
    title: str = Form(..., description="파티 제목 (필수)"),
    description: str = Form(..., description="파티 설명 (필수)"),
    subCategories: List[str] = Form(..., description="서브 카테고리 리스트 (필수)"),
    capacity: int = Form(..., description="최대 인원수 (필수)"),
    place: str = Form(..., description="만남 장소명 (필수)"),
    address: str = Form(..., description="주소 (필수)"),
    subAddress: str | None = Form(None, description="상세 주소 (선택)"),
    x: float = Form(..., description="경도 longitude (필수)"),
    y: float = Form(..., description="위도 latitude (필수)"),
    meetingDate: datetime = Form(..., description="만남 일시 UTC ISO 8601 (필수)"),
    selectedArtistId: int = Form(..., description="선택된 아티스트 ID (필수)"),
    imageOrders: str | None = Form(None, description="이미지 순서 JSON (선택)"),
) -> PodForm:
    """PodForm을 Form 데이터로부터 생성 (파티 생성용 - 모든 필수 필드 포함)"""
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


async def get_pod_form_for_update(
    title: str | None = Form(None, description="파티 제목 (선택)"),
    description: str | None = Form(None, description="파티 설명 (선택)"),
    subCategories: List[str] | None = Form(None, description="서브 카테고리 리스트 (선택)"),
    capacity: int | None = Form(None, description="최대 인원수 (선택)"),
    place: str | None = Form(None, description="만남 장소명 (선택)"),
    address: str | None = Form(None, description="주소 (선택)"),
    subAddress: str | None = Form(None, description="상세 주소 (선택)"),
    x: float | None = Form(None, description="경도 longitude (선택)"),
    y: float | None = Form(None, description="위도 latitude (선택)"),
    meetingDate: datetime | None = Form(None, description="만남 일시 UTC ISO 8601 (선택)"),
    selectedArtistId: int | None = Form(None, description="선택된 아티스트 ID (선택)"),
    imageOrders: str | None = Form(None, description="이미지 순서 JSON (선택)"),
) -> PodForm:
    """PodForm을 Form 데이터로부터 생성 (파티 수정용 - 모든 필드 선택)"""
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
