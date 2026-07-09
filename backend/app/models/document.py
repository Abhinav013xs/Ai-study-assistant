from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), unique=True, nullable=False)
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    total_pages = Column(Integer, default=1, nullable=False)
    language = Column(String, default="en", nullable=False)
    extra_info = Column(JSON, nullable=True)  # Store custom attributes like publication date, etc.

    file = relationship("File", back_populates="metadata_info")

class OcrResult(Base, TimestampMixin):
    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=False)
    layout_data = Column(JSON, nullable=True)  # Store table structures, boxes, OCR confidence maps

    file = relationship("File", back_populates="ocr_results")

class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    vector_id = Column(String, nullable=False, index=True)  # Reference ID of the vector stored in ChromaDB

    file = relationship("File", back_populates="chunks")
