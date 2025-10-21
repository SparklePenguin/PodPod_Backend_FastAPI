"""
사용자 알림 설정 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import time


class UserNotificationSettingsDto(BaseModel):
    """사용자 알림 설정 응답 스키마"""

    id: int = Field(..., alias="id", description="설정 ID")
    user_id: int = Field(..., alias="userId", description="사용자 ID")

    # 알림 카테고리별 설정
    wake_up_alarm: bool = Field(
        ..., alias="wakeUpAlarm", description="기상 알림", default=True
    )
    bus_alert: bool = Field(
        ..., alias="busAlert", description="버스 알림", default=True
    )
    party_alert: bool = Field(
        ..., alias="partyAlert", description="파티 알림", default=True
    )
    community_alert: bool = Field(
        ..., alias="communityAlert", description="커뮤니티 알림", default=True
    )
    product_alarm: bool = Field(
        ..., alias="productAlarm", description="상품 알림", default=True
    )

    # 방해금지 설정
    do_not_disturb_enabled: bool = Field(
        ..., alias="doNotDisturbEnabled", description="방해금지 모드", default=False
    )
    start_time: Optional[str] = Field(
        None, alias="startTime", description="방해금지 시작 시간 (오후 12:00 형식)"
    )
    end_time: Optional[str] = Field(
        None, alias="endTime", description="방해금지 종료 시간 (오후 12:00 형식)"
    )

    # 마케팅 설정
    marketing_enabled: bool = Field(
        ..., alias="marketingEnabled", description="마케팅 알림 수신", default=False
    )

    model_config = {"from_attributes": True, "populate_by_name": True}


class UpdateUserNotificationSettingsRequest(BaseModel):
    """사용자 알림 설정 수정 요청 스키마"""

    wake_up_alarm: Optional[bool] = Field(
        None, alias="wakeUpAlarm", description="기상 알림"
    )
    bus_alert: Optional[bool] = Field(None, alias="busAlert", description="버스 알림")
    party_alert: Optional[bool] = Field(
        None, alias="partyAlert", description="파티 알림"
    )
    community_alert: Optional[bool] = Field(
        None, alias="communityAlert", description="커뮤니티 알림"
    )
    product_alarm: Optional[bool] = Field(
        None, alias="productAlarm", description="상품 알림"
    )
    do_not_disturb_enabled: Optional[bool] = Field(
        None, alias="doNotDisturbEnabled", description="방해금지 모드"
    )
    start_time: Optional[str] = Field(
        None, alias="startTime", description="방해금지 시작 시간"
    )
    end_time: Optional[str] = Field(
        None, alias="endTime", description="방해금지 종료 시간"
    )
    marketing_enabled: Optional[bool] = Field(
        None, alias="marketingEnabled", description="마케팅 알림 수신"
    )

    model_config = {"populate_by_name": True}
