import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"

class OTPPurpose(str, enum.Enum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    
    # Relationships
    otps = relationship("UserOTP", back_populates="user", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="user", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")

class UserOTP(Base, TimestampMixin):
    __tablename__ = "user_otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)
    purpose = Column(Enum(OTPPurpose), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="otps")
