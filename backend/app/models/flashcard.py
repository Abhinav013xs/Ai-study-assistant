from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import datetime

class Flashcard(Base, TimestampMixin):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    difficulty = Column(String, default="medium", nullable=False)  # easy, medium, hard
    topic = Column(String, nullable=True)
    
    # Spaced Repetition Fields (SuperMemo SM-2 algorithm)
    next_review = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)
    interval = Column(Integer, default=0, nullable=False)  # in days
    ease_factor = Column(Float, default=2.5, nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)

    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="flashcards")
