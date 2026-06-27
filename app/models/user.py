from sqlalchemy import Column, String, UUID, DateTime, Boolean, Time, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timedelta
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    whatsapp_phone = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    role = Column(String)
    timezone = Column(String, default="UTC")
    work_start_time = Column(Time)
    work_end_time = Column(Time)
    checkin_preference = Column(SQLEnum('morning', 'evening', 'none', name='checkin_preference'), default='morning')
    google_calendar_connected = Column(Boolean, default=False)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)
    top_priorities = Column(JSON)
    subscription_status = Column(SQLEnum('trial', 'active', 'expired', 'cancelled', name='subscription_status'), default='trial')
    trial_ends_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow() + timedelta(days=14))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    projects = relationship("Project", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    events = relationship("Event", back_populates="user")
    reviews = relationship("WeeklyReview", back_populates="user")

