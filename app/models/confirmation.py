from sqlalchemy import Column, String, UUID, DateTime
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class PendingConfirmation(Base):
    __tablename__ = "pending_confirmations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    whatsapp_phone = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False) # e.g. "delete_task", "delete_event"
    resource_id = Column(String, nullable=True)
    resource_title = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
