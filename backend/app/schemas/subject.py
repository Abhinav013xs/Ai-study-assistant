from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.subject import FileStatus, OCRStatus

# --- Subject Schemas ---
class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#4F46E5"

class SubjectCreate(SubjectBase):
    pass

class SubjectOut(SubjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- File Schemas ---
class FileBase(BaseModel):
    name: str
    mime_type: str
    file_size: int
    status: FileStatus
    ocr_status: OCRStatus
    subject_id: Optional[int] = None

class FileOut(FileBase):
    id: int
    user_id: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
