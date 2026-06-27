from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_by_phone(self, whatsapp_phone: str, name: str = None) -> User:
        user = self.db.query(User).filter(User.whatsapp_phone == whatsapp_phone).first()
        if not user:
            user = User(
                whatsapp_phone=whatsapp_phone,
                name=name or "User",
                subscription_status="trial"
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    def update(self, user_id: UUID, data: UserUpdate) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user
