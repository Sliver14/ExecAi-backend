from sqlalchemy import Column, String, UUID, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_text = Column(String, nullable=False)
    is_from_user = Column(Boolean, nullable=False)
    intent_detected = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
