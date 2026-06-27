from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time
from uuid import UUID

class UserBase(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    timezone: Optional[str] = "UTC"
    work_start_time: Optional[time] = None
    work_end_time: Optional[time] = None
    checkin_preference: Optional[str] = "morning"
    google_calendar_connected: Optional[bool] = False
    top_priorities: Optional[List[str]] = None

class UserCreate(UserBase):
    whatsapp_phone: str

class UserUpdate(UserBase):
    pass

class User(UserBase):
    id: UUID
    whatsapp_phone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
