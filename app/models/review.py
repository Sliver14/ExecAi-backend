from sqlalchemy import Column, String, UUID, DateTime, Integer, JSON, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class WeeklyReview(Base):
    __tablename__ = "weekly_reviews"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_start = Column(Date, nullable=False)
    completed_tasks = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    insights = Column(JSON)
    reflection = Column(JSON)
    planned_priorities = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reviews")
