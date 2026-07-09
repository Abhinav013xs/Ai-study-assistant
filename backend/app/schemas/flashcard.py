from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class FlashcardBase(BaseModel):
    front: str
    back: str
    difficulty: Optional[str] = "medium"
    topic: Optional[str] = None
    subject_id: Optional[int] = None

class FlashcardCreate(FlashcardBase):
    pass

class FlashcardOut(FlashcardBase):
    id: int
    user_id: int
    next_review: datetime
    interval: int
    ease_factor: float
    repetitions: int
    created_at: datetime

    class Config:
        from_attributes = True

class FlashcardReview(BaseModel):
    rating: int = Field(..., ge=0, le=5)  # Quality score 0-5 for SM-2 spaced repetition
