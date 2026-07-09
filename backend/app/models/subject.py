import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class FileStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class OCRStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, default="#4F46E5", nullable=False)  # Tailwind indigo-600 default
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="subjects")
    files = relationship("File", back_populates="subject", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="subject", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="subject", cascade="all, delete-orphan")

class File(Base, TimestampMixin):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)  # Storage path (local path or S3 key)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # size in bytes
    status = Column(Enum(FileStatus), default=FileStatus.UPLOADING, nullable=False)
    ocr_status = Column(Enum(OCRStatus), default=OCRStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="files")
    subject = relationship("Subject", back_populates="files")
    
    metadata_info = relationship("DocumentMetadata", back_populates="file", uselist=False, cascade="all, delete-orphan")
    ocr_results = relationship("OcrResult", back_populates="file", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")
    citations = relationship("MessageCitation", back_populates="file", cascade="all, delete-orphan")
