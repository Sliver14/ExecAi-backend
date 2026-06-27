from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.models.user import User

def get_or_create_user(db: Session, whatsapp_phone: str) -> User:
    service = UserService(db)
    return service.get_or_create_by_phone(whatsapp_phone)
