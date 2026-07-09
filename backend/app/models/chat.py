import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class MessageSender(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Conversation", nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    subject = relationship("Subject", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(Enum(MessageSender), nullable=False)
    content = Column(Text, nullable=False)
    audio_url = Column(String, nullable=True)  # URL to TTS audio file if generated

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("MessageCitation", back_populates="message", cascade="all, delete-orphan")

class MessageCitation(Base, TimestampMixin):
    __tablename__ = "message_citations"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=True)
    snippet = Column(Text, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="citations")
    file = relationship("File", back_populates="citations")

    @property
    def file_name(self) -> str:
        return self.file.name if self.file else "Document"

