from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """알림 기본 스키마"""

    title: str = Field()
    body: str = Field()
    type: str = Field()
    value: str = Field()
    related_id: int | None = Field(default=None, alias="relatedId")
