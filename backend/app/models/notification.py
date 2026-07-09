from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    notification_type = Column(String, default="info", nullable=False)  # system, streak, alert, reminder
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")

class Feedback(Base, TimestampMixin):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)  # 1 to 5 stars
    comments = Column(Text, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="feedback")
