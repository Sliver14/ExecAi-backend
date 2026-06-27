from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class EventBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    google_calendar_event_id: Optional[str] = None
    reminder_minutes: Optional[int] = 30

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    google_calendar_event_id: Optional[str] = None
    reminder_minutes: Optional[int] = None

class Event(EventBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
