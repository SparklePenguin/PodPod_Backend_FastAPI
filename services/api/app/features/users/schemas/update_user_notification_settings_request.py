from pydantic import BaseModel, Field


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
