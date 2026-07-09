from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

# --- Notification Schemas ---
class NotificationOut(BaseModel):
    id: int
    title: str
    content: str
    is_read: bool
    notification_type: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Feedback Schemas ---
class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None

class FeedbackOut(BaseModel):
    id: int
    user_id: int
    rating: int
    comments: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
