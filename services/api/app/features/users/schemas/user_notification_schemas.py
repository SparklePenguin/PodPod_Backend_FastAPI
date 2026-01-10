"""사용자 알림 설정 관련 스키마"""

from pydantic import BaseModel, Field


class UserNotificationSettingsDto(BaseModel):
    """사용자 알림 설정 응답 스키마"""

    id: int = Field(..., description="설정 ID")
    user_id: int = Field(..., alias="userId", description="사용자 ID")

    # 알림 카테고리별 설정
    wake_up_alarm: bool = Field(
        default=True, alias="wakeUpAlarm", description="기상 알림"
    )
    bus_alert: bool = Field(default=True, alias="busAlert", description="버스 알림")
    party_alert: bool = Field(default=True, alias="partyAlert", description="파티 알림")
    community_alert: bool = Field(
        default=True, alias="communityAlert", description="커뮤니티 알림"
    )
    product_alarm: bool = Field(
        default=True, alias="productAlarm", description="상품 알림"
    )

    # 방해금지 설정
    do_not_disturb_enabled: bool = Field(
        default=False,
        alias="doNotDisturbEnabled",
        description="방해금지 모드",
    )
    start_time: int | None = Field(
        None,
        alias="startTime",
        description="방해금지 시작 시간 (timestamp)",
    )
    end_time: int | None = Field(
        None,
        alias="endTime",
        description="방해금지 종료 시간 (timestamp)",
    )

    # 마케팅 설정
    marketing_enabled: bool = Field(
        default=False,
        alias="marketingEnabled",
        description="마케팅 알림 수신",
    )

    model_config = {"from_attributes": True, "populate_by_name": True}


class UpdateUserNotificationSettingsRequest(BaseModel):
    """사용자 알림 설정 수정 요청 스키마"""

    wake_up_alarm: bool | None = Field(
        None, alias="wakeUpAlarm", description="기상 알림"
    )
    bus_alert: bool | None = Field(None, alias="busAlert", description="버스 알림")
    party_alert: bool | None = Field(None, alias="partyAlert", description="파티 알림")
    community_alert: bool | None = Field(
        None, alias="communityAlert", description="커뮤니티 알림"
    )
    product_alarm: bool | None = Field(
        None, alias="productAlarm", description="상품 알림"
    )
    do_not_disturb_enabled: bool | None = Field(
        None, alias="doNotDisturbEnabled", description="방해금지 모드"
    )
    start_time: int | None = Field(
        None,
        alias="startTime",
        description="방해금지 시작 시간 (timestamp)",
    )
    end_time: int | None = Field(
        None,
        alias="endTime",
        description="방해금지 종료 시간 (timestamp)",
    )
    marketing_enabled: bool | None = Field(
        None, alias="marketingEnabled", description="마케팅 알림 수신"
    )

    model_config = {"populate_by_name": True}
