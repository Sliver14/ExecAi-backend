from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from ..models.event import Event
from ..schemas.event import EventCreate, EventUpdate

class EventService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: UUID, data: EventCreate) -> Event:
        event = Event(user_id=user_id, **data.model_dump())
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_user_events(self, user_id: UUID) -> List[Event]:
        return self.db.query(Event).filter(
            Event.user_id == user_id,
            Event.deleted_at.is_(None)
        ).all()
