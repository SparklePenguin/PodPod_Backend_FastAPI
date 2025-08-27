from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    profile_image: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    profile_image: Optional[str] = None


class UserResponse(UserBase):
    id: int
    auth_provider: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
