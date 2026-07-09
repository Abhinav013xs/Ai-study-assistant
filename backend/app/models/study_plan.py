from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class StudyPlan(Base, TimestampMixin):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    daily_hours = Column(Integer, default=2, nullable=False)
    schedule_json = Column(JSON, nullable=False)  # Stores generated list of tasks by date/week
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="study_plans")

class StudySession(Base, TimestampMixin):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)  # Studied duration
    notes = Column(Text, nullable=True)

    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="study_sessions")
    subject = relationship("Subject")
