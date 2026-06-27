from sqlalchemy.orm import Session
from typing import TypeVar, Generic, List, Optional
from datetime import datetime
from uuid import UUID

T = TypeVar("T")

class BaseService(Generic[T]):
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model

    def get(self, id: UUID) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id, self.model.deleted_at.is_(None)).first()

    def get_by_user(self, user_id: UUID) -> List[T]:
        return self.db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.deleted_at.is_(None)
        ).all()
